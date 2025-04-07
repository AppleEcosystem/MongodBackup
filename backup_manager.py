#!/usr/bin/env python3
import os
import subprocess
import logging
import aioboto3
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED
from config import R2_BUCKET, R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
from progress_tracker import ProgressTracker

# Configure logging
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, telegram_notifier):
        self.telegram = telegram_notifier
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.backup_dir = f"/tmp/mongodb_backup_{self.timestamp}"
        self.backup_zip = f"/tmp/mongodb_backup_{self.timestamp}.zip"
        self.telegram.backup_info = {
            'timestamp': self.timestamp,
            'backup_path': self.backup_zip
        }

    async def dump_mongodb(self):
        """Dump all MongoDB databases"""
        try:
            status = "🔍 <b>Starting MongoDB Backup</b>\n\n" \
                    f"⏳ <b>Status:</b> Dumping databases..."
            await self.telegram.update_message(status)

            os.makedirs(self.backup_dir, exist_ok=True)
            result = subprocess.run(
                ['mongodump', f'--out={self.backup_dir}', '--quiet'],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise Exception(f"MongoDB dump failed: {result.stderr}")

            status = "🗄️ <b>MongoDB Dump Complete</b>\n\n" \
                    f"📂 <b>Location:</b> <code>{self.backup_dir}</code>\n" \
                    "⏳ <b>Status:</b> Compressing backup..."
            await self.telegram.update_message(status)

            return True
        except Exception as e:
            logger.error(f"Dump error: {str(e)}")
            raise

    async def create_max_compression_zip(self):
        """Create ZIP with maximum compression"""
        try:
            if subprocess.run(['which', 'zip'], capture_output=True).returncode == 0:
                result = subprocess.run(
                    ['zip', '-9', '-r', self.backup_zip, '.'],
                    cwd=self.backup_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise Exception(f"zip command failed: {result.stderr}")
            else:
                with ZipFile(self.backup_zip, 'w', ZIP_DEFLATED, compresslevel=9) as zipf:
                    for root, dirs, files in os.walk(self.backup_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.backup_dir)
                            zipf.write(file_path, arcname)

            zip_size = os.path.getsize(self.backup_zip)
            original_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                             for dirpath, _, filenames in os.walk(self.backup_dir)
                             for filename in filenames)
            compression_ratio = (1 - (zip_size / original_size)) * 100

            # Store backup info before cleanup
            self.telegram.backup_info.update({
                'size_mb': zip_size/1024/1024,
                'compression': compression_ratio,
                'filename': os.path.basename(self.backup_zip)
            })

            status = "📦 <b>Backup Compressed</b>\n\n" \
                    f"📁 <b>File:</b> <code>{self.backup_zip}</code>\n" \
                    f"📊 <b>Size:</b> {zip_size/1024/1024:.2f} MB ({compression_ratio:.1f}% compression)\n" \
                    "⏳ <b>Status:</b> Starting upload..."
            await self.telegram.update_message(status)

            return True
        except Exception as e:
            logger.error(f"ZIP creation failed: {str(e)}")
            raise

    async def upload_to_r2(self):
        """Upload with progress tracking"""
        try:
            file_size = os.path.getsize(self.backup_zip)
            progress_tracker = ProgressTracker(file_size, self.telegram)

            async with aioboto3.Session().client(
                's3',
                endpoint_url=R2_ENDPOINT,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY
            ) as client:
                if file_size > 50 * 1024 * 1024:
                    mpu = await client.create_multipart_upload(
                        Bucket=R2_BUCKET,
                        Key=os.path.basename(self.backup_zip)
                    )

                    parts = []
                    part_number = 1
                    with open(self.backup_zip, 'rb') as f:
                        while chunk := f.read(50 * 1024 * 1024):
                            part = await client.upload_part(
                                Bucket=R2_BUCKET,
                                Key=os.path.basename(self.backup_zip),
                                PartNumber=part_number,
                                UploadId=mpu['UploadId'],
                                Body=chunk
                            )
                            parts.append({
                                'PartNumber': part_number,
                                'ETag': part['ETag']
                            })
                            await progress_tracker.update(len(chunk))
                            part_number += 1

                    await client.complete_multipart_upload(
                        Bucket=R2_BUCKET,
                        Key=os.path.basename(self.backup_zip),
                        UploadId=mpu['UploadId'],
                        MultipartUpload={'Parts': parts}
                    )
                else:
                    with open(self.backup_zip, 'rb') as f:
                        await client.put_object(
                            Bucket=R2_BUCKET,
                            Key=os.path.basename(self.backup_zip),
                            Body=f
                        )
                    await progress_tracker.update(file_size)

            return True
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise

    async def cleanup(self):
        """Remove temporary files"""
        try:
            if os.path.exists(self.backup_dir):
                subprocess.run(['rm', '-rf', self.backup_dir], check=True)
            logger.info("Temporary files cleaned up")
            return None
        except Exception as e:
            logger.warning(f"Cleanup warning: {str(e)}")
            return str(e)
