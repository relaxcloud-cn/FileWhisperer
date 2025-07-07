"""
邮件文档处理模块
"""
import email
from typing import List
from loguru import logger

from ..dt import Node, File, Data
from .utils import encode_binary


class EmailExtractor:
    
    @staticmethod
    def extract_email_file(node: Node) -> List[Node]:
        nodes = []
        file: File
        if isinstance(node.content, File):
            file = node.content
        elif isinstance(node.content, Data):
            logger.error("extract_email_file enter Data type")
            return nodes
        
        # 解析邮件内容
        msg = email.message_from_bytes(file.content)
        
        # 添加邮件头信息
        header_data = {}
        for key in ['From', 'To', 'Subject', 'Date', 'Message-ID']:
            value = msg.get(key)
            if value:
                header_data[key] = value
        
        # 创建邮件头信息节点
        if header_data:
            header_text = "\n".join([f"{k}: {v}" for k, v in header_data.items()])
            header_node = Node()
            header_node.id = 0
            header_node.content = Data(type="EMAIL_HEADER", content=encode_binary(header_text))
            header_node.prev = node
            header_node.inherit_limits(node)
            nodes.append(header_node)
        
        # 提取邮件正文和附件
        attachment_count = 0
        body_parts = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # 处理附件
                if 'attachment' in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachment_count += 1
                        attachment_data = part.get_payload(decode=True)
                        if attachment_data:
                            attachment_node = Node()
                            attachment_node.content = File(
                                path=filename,
                                name=filename,
                                content=attachment_data
                            )
                            attachment_node.prev = node
                            attachment_node.inherit_limits(node)
                            nodes.append(attachment_node)
                
                # 处理邮件正文
                elif content_type in ['text/plain', 'text/html']:
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            text_content = payload.decode(charset, errors='ignore')
                            body_parts.append({
                                'type': content_type,
                                'content': text_content
                            })
                        except Exception as e:
                            logger.warning(f"Failed to decode email body part: {e}")
        else:
            # 单部分邮件
            payload = msg.get_payload(decode=True)
            if payload:
                try:
                    charset = msg.get_content_charset() or 'utf-8'
                    text_content = payload.decode(charset, errors='ignore')
                    content_type = msg.get_content_type()
                    body_parts.append({
                        'type': content_type,
                        'content': text_content
                    })
                except Exception as e:
                    logger.warning(f"Failed to decode email body: {e}")
        
        # 创建邮件正文节点
        for i, body_part in enumerate(body_parts):
            body_node = Node()
            body_node.id = i + 1
            data_type = "EMAIL_TEXT" if body_part['type'] == 'text/plain' else "EMAIL_HTML"
            body_node.content = Data(type=data_type, content=encode_binary(body_part['content']))
            body_node.prev = node
            body_node.inherit_limits(node)
            nodes.append(body_node)
        
        # 添加统计信息到元数据
        node.meta.map_number["attachment_count"] = attachment_count
        node.meta.map_number["body_parts_count"] = len(body_parts)
        
        return nodes