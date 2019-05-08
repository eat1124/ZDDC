"""
python实现FTP上传下载文件
"""
from ftplib import FTP


class FileHandler(object):
    def __init__(self):
        self.server = "192.168.85.130"
        self.user = "Administrator"
        self.password = "password"

    def ftp_connect(self):
        ftp = FTP()
        ftp.set_debuglevel(2)
        ftp.connect(self.server, 21)
        ftp.login(self.user, self.password)
        return ftp

    def download_file(self, ftp, remotepath, localpath):
        bufsize = 1024
        fp = open(localpath,'wb')
        ftp.retrbinary('RETR '+ remotepath, fp.write,bufsize)
        # 接受服务器上文件并写入文本
        ftp.set_debuglevel(0) # 关闭调试
        fp.close() # 关闭文件

    def upload_file(self, ftp, remotepath, localpath=None, fp=None):
        bufsize = 1024
        # 如果上传的是二进制数据，则跳过
        if not fp:
            fp = open(localpath,'rb')
        response_code = ftp.storbinary('STOR '+ remotepath, fp, bufsize) # 上传文件
        ftp.set_debuglevel(0)
        fp.close()


if __name__ == "__main__":
    file_handler = FileHandler()
    ftp = file_handler.ftp_connect()
    # file_handler.download_file(ftp, r"docker.py", r"C:\Users\Administrator\Desktop\docker.py")
    file_handler.upload_file(ftp, r"docker.py", localpath=r"C:\Users\Administrator\Desktop\Pros\docker.py")

    ftp.quit()