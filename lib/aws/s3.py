#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" module description """

__author__ = "tarun mudgal"

import mimetypes
import os

import boto3


class S3Client:
    """
    S3Client (AWS S3 client) that interacts with AWS S3 APIs
    """

    __single_instance = None

    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str) -> None:
        """Initializes singleton S3Client that is used to make AWS S3 API calls
        Args:
            aws_access_key_id: aws access key id for authentication
            aws_secret_access_key: aws access key secret for authentication
        Raises:
            Exception
        Returns:
            S3Client object
        """

        if S3Client.__single_instance is not None:
            raise Exception("S3Client is a singleton class and cannot have more than one objects")

        S3Client.__single_instance = self

        self.client = boto3.client(
            "s3", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
        )

        self.resource = boto3.resource(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            config=boto3.session.Config(signature_version="s3"),
        )

    def copy_file_on_s3(
        self, bucket_name: str, src_fpath: str = None, s3_fpath: str = None
    ) -> bool:
        """copies file on S3 bucket
        Args:
          bucket_name: S3 bucket name
          src_fpath: file-path that need to be copied to S3 bucket
          s3_fpath: S3 file-path relative to S3 bucket bucket_name where src_fpath would be copied

        Returns:
            copy_status (True or False)
        """
        copy_status = False
        if src_fpath:
            s3_conf = myconfig.get("aws").get("s3")
            try:
                self.client.upload_file(
                    Filename=src_fpath, Bucket=bucket_name, Key=s3_fpath,
                )
                copy_status = True
                mylog.info("file {} successfully copied on s3 at {}".format(src_fpath, s3_fpath))
            except Exception as fault:
                mylog.error("file {} could not be copied on S3. Error={}".format(src_fpath, fault))
                mylog.exception(fault)
        else:
            mylog.debug("nothing to copy on S3")

        return copy_status

    def if_key_exists(self, bucket: str, key: str) -> bool:
        """checks if a key exists on s3 bucket
        Args:
          bucket: S3 bucket name
          key: s3 bucket key that needs to be looked at

        Returns:
            True or False
        """
        response = self.client.list_objects_v2(Bucket=bucket, Prefix=key,)
        if response.get("Contents", []):
            return True

        return False

    def download_files_from_s3(self, bucket: str, key: str, download_path: str = ".") -> None:
        """downloads file or directories from s3 to local dir
        Args:
          bucket: S3 bucket name
          key: s3 bucket key that needs to be downloaded locally
          download_path: local path where files are downloaded

        Returns:
            None
        """
        try:

            response = self.client.list_objects_v2(Bucket=bucket, Prefix=key,)
            if not download_path.endswith(os.path.basename(key)):
                download_path = download_path + os.path.sep + os.path.basename(key)

            if not os.path.exists(download_path):
                os.makedirs(download_path)

            for obj in response.get("Contents", []):
                local_path = download_path + os.path.sep + os.path.basename(obj["Key"])
                # print("local_path={}".format(local_path))
                self.client.download_file(bucket, obj["Key"], local_path)
        except Exception as fault:
            mylog.exception(fault)

    def upload_files_to_s3(
        self, bucket: str, key: str, src: str, skip_parent_dir_creation: bool = False
    ) -> None:
        """uploads file or directories from local src dir to s3 bucket key
        Args:
          bucket: S3 bucket name
          key: s3 bucket key where file or directories would be downloaded
          src: local path from where files are uploaded
          skip_parent_dir_creation: if enabled, first parent dir is not created on s3 e.g. if src=allure/html and
          key=test-workload and if skip_parent_dir_creation=True, html dir would not be copied inside test-workload

        Returns:
            None
        """
        try:
            if not os.path.exists(src):
                raise FileNotFoundError("src={} does not exist locally".format(src))

            key = key.rstrip("/")
            src = src.rstrip("/")

            if os.path.isfile(src):
                key = key + "/" + os.path.basename(src)
                self.client.upload_file(
                    Filename=src, Bucket=bucket, Key=key,
                )
            else:
                root = None
                for dpath, dnames, fnames in os.walk(src, topdown=True):
                    if root is None:
                        if not skip_parent_dir_creation:
                            root = os.path.dirname(dpath.rstrip(os.path.sep))
                        else:
                            root = dpath.rstrip(os.path.sep)

                    key1 = (
                        key.rstrip("/")
                        + "/"
                        + dpath.replace(root, "").lstrip(os.path.sep).replace(os.path.sep, "/")
                    )
                    for fname in fnames:
                        key2 = key1.rstrip("/") + "/" + fname
                        src1 = dpath + os.path.sep + fname
                        file_mimetype = mimetypes.MimeTypes().guess_type(src1)[0]
                        mylog.debug(
                            "copying src={} file with mimetype={} to s3 key={}".format(
                                src1, file_mimetype, key2
                            )
                        )
                        self.client.upload_file(
                            Filename=src1,
                            Bucket=bucket,
                            Key=key2,
                            ExtraArgs={"ContentType": file_mimetype, "ACL": "public-read"},
                        )
        except Exception as fault:
            mylog.exception(fault)

    def copy_files_on_s3_from_src_key(self, bucket: str, src_key: str, dest_key: str) -> None:
        """copies src_key files (that matches src_key as prefix) to dest key
        Args:
          bucket: S3 bucket name
          src_key: key name that is used as a prefix to select all the keys that starts with this key name
          dest_key: key name where you want to copy files to

        Returns:
            None
        """
        try:
            bucket_obj = self.resource.Bucket(bucket)
            for obj in bucket_obj.objects.filter(Prefix=src_key):
                if not obj.key.endswith("/"):
                    fname = obj.key.split("/")[-1]
                    dest_file_key = dest_key + "/" + fname
                    src_file_key = bucket + "/" + obj.key
                    self.resource.Object(bucket, dest_file_key).copy_from(CopySource=src_file_key)
        except Exception as fault:
            mylog.exception(fault)

    def delete_files_from_s3(self, bucket: str, key: str) -> None:
        """deletes all keys that starts with key prefix
        Args:
          bucket: S3 bucket name
          key: key name that is used as a prefix to delete all the keys that starts with this key name

        Returns:
            None
        """
        try:
            bucket = self.resource.Bucket(bucket)
            bucket.objects.filter(Prefix=key).delete()
        except Exception as fault:
            mylog.exception(fault)
