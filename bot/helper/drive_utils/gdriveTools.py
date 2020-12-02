import os
import pickle

import requests
import logging

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from telegram import InlineKeyboardMarkup
from bot.helper.telegram_helper import button_builder
from bot import DRIVE_NAME, DRIVE_ID, INDEX_URL, telegra_ph

LOGGER = logging.getLogger(__name__)
logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
TELEGRAPHLIMIT = 95

class GoogleDriveHelper:
    def __init__(self, name=None, listener=None):
        self.__G_DRIVE_TOKEN_FILE = "token.pickle"
        # Check https://developers.google.com/drive/scopes for all available scopes
        self.__OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
        self.__service = self.authorize()
        self.telegraph_content = []
        self.path = []

    def get_readable_file_size(self,size_in_bytes) -> str:
        if size_in_bytes is None:
            return '0B'
        index = 0
        size_in_bytes = int(size_in_bytes)
        while size_in_bytes >= 1024:
            size_in_bytes /= 1024
            index += 1
        try:
            return f'{round(size_in_bytes, 2)}{SIZE_UNITS[index]}'
        except IndexError:
            return 'File too large'

    def authorize(self):
        # Get credentials
        credentials = None
        if os.path.exists(self.__G_DRIVE_TOKEN_FILE):
            with open(self.__G_DRIVE_TOKEN_FILE, 'rb') as f:
                credentials = pickle.load(f)
        if credentials is None or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.__OAUTH_SCOPE)
                LOGGER.info(flow)
                credentials = flow.run_console(port=0)

            # Save the credentials for the next run
            with open(self.__G_DRIVE_TOKEN_FILE, 'wb') as token:
                pickle.dump(credentials, token)
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def drive_query(self, parent_id, fileName):
        query = f"'{parent_id}' in parents and (name contains '{fileName}')"
        response = self.__service.files().list(supportsTeamDrives=True,
                                               includeTeamDriveItems=True,
                                               q=query,
                                               spaces='drive',
                                               pageSize=200,
                                               fields='files(id, name, mimeType, size)',
                                               orderBy='modifiedTime desc').execute()["files"]
        return response

    def escapes(self, str):
        chars = ['\\', "'", '"', r'\a', r'\b', r'\f', r'\n', r'\r', r'\t']
        for char in chars:
            str = str.replace(char, '\\'+char)
        return str

    def edit_telegraph(self):
        nxt_page = 1 
        prev_page = 0
        for content in self.telegraph_content :
            if nxt_page == 1 :
                content += f'<b><a href="https://telegra.ph/{self.path[nxt_page]}">Nᴇxᴛ👉</a></b>'
                nxt_page += 1
            else :
                if prev_page <= self.num_of_path:
                    content += f'<b><a href="https://telegra.ph/{self.path[prev_page]}">👈Pʀᴇᴠɪᴏᴜs</a></b>'
                    prev_page += 1
                if nxt_page < self.num_of_path:
                    content += f'<b> | <a href="https://telegra.ph/{self.path[nxt_page]}">Nᴇxᴛ👉</a></b>'
                    nxt_page += 1
            telegra_ph.edit_page(path = self.path[prev_page],
                                 title = 'Vɪᴋɪɴɢs Sᴇᴀʀᴄʜ Iɴᴅᴇx',
                                 html_content=content)
        return

    def escapes(self, str):
        chars = ['\\', "'", '"', r'\a', r'\b', r'\f', r'\n', r'\r', r'\t']
        for char in chars:
            str = str.replace(char, '\\'+char)
        return str
    
    def drive_list(self, fileName):
        msg = ''
        INDEX = -1
        content_count = 0
        add_title_msg = True
        for parent_id in DRIVE_ID :
            response = self.drive_query(parent_id, fileName)    
            INDEX += 1          
            if response:
                if add_title_msg == True:
                    msg = f'<h3>Sᴇᴀʀᴄʜ Rᴇsᴜʟᴛs Fᴏʀ Yᴏᴜʀ Kᴇʏᴡᴏʀᴅ : {fileName}</h3><br>𝐌𝐢𝐫𝐫𝐨𝐫𝐫𝐳<br><br>'
                    add_title_msg = False
                msg += f"╾────────────╼<br><b>{DRIVE_NAME[INDEX]}</b><br>╾────────────╼<br>"
                for file in response:
                    if file.get('mimeType') == "application/vnd.google-apps.folder":  # Detect Whether Current Entity is a Folder or File.
                        msg += f"🗃️<code>{file.get('name')}</code> <b>(Folder)</b><br>" \
                               f"<b><a href='https://drive.google.com/drive/folders/{file.get('id')}'>Drive Link</a></b>"
                        if INDEX_URL[INDEX] is not None:
                            url_path = requests.utils.quote(f'{file.get("name")}')
                            url = f'{INDEX_URL[INDEX]}/{url_path}/'
                            msg += f'<b> | <a href="{url}">Index Link</a></b>'
                    else:
                        msg += f"🌀<code>{file.get('name')}</code> <b>({self.get_readable_file_size(file.get('size'))})</b><br>" \
                               f"<b><a href='https://drive.google.com/uc?id={file.get('id')}&export=download'>Drive Link</a></b>"
                        if INDEX_URL[INDEX] is not None:
                            url_path = requests.utils.quote(f'{file.get("name")}')
                            url = f'{INDEX_URL[INDEX]}/{url_path}'
                            msg += f'<b> | <a href="{url}">Index Link</a></b>'
                    msg += '<br><br>'
                    content_count += 1
                    if content_count == TELEGRAPHLIMIT :
                       self.telegraph_content.append(msg)
                       msg = ""
                       content_count = 0

        if msg != '':
            self.telegraph_content.append(msg)

        if len(self.telegraph_content) == 0:
            return "<b>Nᴏ Rᴇsᴜʟᴛs Fᴏᴜɴᴅ Fᴏʀ Yᴏᴜʀ Fɪʟᴇ Nᴀᴍᴇ Kᴇʏᴡᴏʀᴅ:(</b>", None

        for content in self.telegraph_content :
            self.path.append(telegra_ph.create_page(title = 'Vɪᴋɪɴɢs Sᴇᴀʀᴄʜ Iɴᴅᴇx',
                                                html_content=content )['path'])

        self.num_of_path = len(self.path)      
        if self.num_of_path > 1:
            self.edit_telegraph()

        msg = f" <b>Sᴇᴀʀᴄʜ Rᴇsᴜʟᴛs Fᴏʀ Yᴏᴜʀ Kᴇʏᴡᴏʀᴅ :</b> ➼ {fileName} 👇 "
        buttons = button_builder.ButtonMaker()   
        buttons.buildbutton("☘️ 𝐂𝐥𝐢𝐜𝐤 𝐇𝐞𝐫𝐞😋", f"https://telegra.ph/{self.path[0]}")

        return msg, InlineKeyboardMarkup(buttons.build_menu(1))
