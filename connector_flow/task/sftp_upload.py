# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 initOS GmbH & Co. KG (<http://www.initos.com>).
#                  2015 FactorLibre (http://www.factorlibre.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
from .ftp_upload import ftp_upload
import paramiko
import logging
import errno
_logger = logging.getLogger(__name__)


class sftp_upload(ftp_upload):
    """FTP Configuration options:
     - host, user, password, port (22 by default)
     - upload_directory:  directory on the FTP server where files are
                          uploaded to
    """

    def _handle_existing_target(self, sftp_conn, target_name, filedata):
        raise Exception("%s already exists" % target_name)

    def _handle_new_target(self, sftp_conn, target_name, filedata):
        with sftp_conn.open(target_name, 'w') as fileobj:
            fileobj.write(filedata)
            _logger.info('wrote %s, size %d', target_name, len(filedata))

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
            sftp_conn.stat(target_name)
            self._handle_existing_target(sftp_conn, target_name, filedata)
        except IOError, e:
            if e.errno == errno.ENOENT:
                self._handle_new_target(sftp_conn, target_name, filedata)

        sftp_conn.close()
        transport.close()


class sftp_upload_task(orm.Model):
    _inherit = 'impexp.task'

    def _get_available_tasks(self, cr, uid, context=None):
        return super(sftp_upload_task, self) \
            ._get_available_tasks(cr, uid, context=context) \
            + [('sftp_upload', 'SFTP Upload')]

    _columns = {
        'task': fields.selection(_get_available_tasks, string='Task',
                                 required=True),
    }

    def sftp_upload_class(self):
        return sftp_upload
