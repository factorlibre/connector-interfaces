# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api
from .ftp_upload import FtpUpload
import errno
import logging
import paramiko
_logger = logging.getLogger(__name__)


class SftpUpload(FtpUpload):
    def _upload_file(self, config, filename, filedata):
        ftp_config = config['ftp']
        upload_directory = ftp_config.get('upload_directory', '')
        port = ftp_config.get('port', 22)

        transport = paramiko.Transport((ftp_config['host'], port))
        transport.connect(
            username=ftp_config['user'],
            password=ftp_config['password'])

        sftp_conn = paramiko.SFTPClient.from_transport(transport)

        target_name = self._target_name(sftp_conn,
                                        upload_directory,
                                        filename)
        try:
            sftp_conn.chdir(upload_directory)
        except IOError, e:
            if e.errno == errno.ENOENT:
                self._handle_not_existing_directory(
                    sftp_conn, upload_directory, filedata)
        try:
            sftp_conn.stat(target_name)
            self._handle_existing_target(sftp_conn, target_name, filedata)
        except IOError, e:
            if e.errno == errno.ENOENT:
                self._handle_new_target(sftp_conn, target_name, filedata)

        sftp_conn.close()
        transport.close()

    def _handle_not_existing_directory(self, ftp_conn, upload_directory,
                                       filedata):
        raise Exception(
            "The directory '{}' does not exist.".format(upload_directory))


class SftpUploadTask(models.Model):
    _inherit = 'impexp.task'

    @api.model
    def _get_available_tasks(self):
        return super(SftpUploadTask, self)._get_available_tasks() + [
            ('sftp_upload', 'SFTP Upload')]

    def sftp_upload_class(self):
        return SftpUpload
