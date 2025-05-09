import json
import re
from typing import Any, Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.send import SendEmailToolParameters, send_mail


class SendMailTool(Tool):
    def _invoke(
            self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        invoke tools
        """
        sender = self.runtime.credentials.get("email_account", "")
        email_rgx = re.compile("^[a-zA-Z0-9._-]+@[a-zA-Z0-9_-]+(\\.[a-zA-Z0-9_-]+)+$")
        password = self.runtime.credentials.get("email_password", "")
        smtp_server = self.runtime.credentials.get("smtp_server", "")
        if not smtp_server:
            yield self.create_text_message("please input smtp server")
            return
        smtp_port = self.runtime.credentials.get("smtp_port", "")
        try:
            smtp_port = int(smtp_port)
        except ValueError:
            yield self.create_text_message("Invalid parameter smtp_port(should be int)")
            return
        if not sender:
            yield self.create_text_message("please input sender")
            return
        if not email_rgx.match(sender):
            yield self.create_text_message("Invalid parameter userid, the sender is not a mailbox")
            return
        receivers_email = tool_parameters["send_to"]
        if not receivers_email:
            yield self.create_text_message("please input receiver email")
            return
        receivers_email = json.loads(receivers_email)
        for receiver in receivers_email:
            if not email_rgx.match(receiver):
                yield self.create_text_message(
                    f"Invalid parameter receiver email, the receiver email({receiver}) is not a mailbox"
                )
                return
        email_content = tool_parameters.get("email_content", "")
        if not email_content:
            yield self.create_text_message("please input email content")
            return
        subject = tool_parameters.get("subject", "")
        if not subject:
            yield self.create_text_message("please input email subject")
            return
        encrypt_method = self.runtime.credentials.get("encrypt_method", "")
        if not encrypt_method:
            yield self.create_text_message("please input encrypt method")
            return
        cc_email = tool_parameters.get('cc', '')
        cc_email_list = []
        if cc_email:
            cc_email_list = json.loads(cc_email)
            for cc_email_item in cc_email_list:
                if not email_rgx.match(cc_email_item):
                    yield self.create_text_message(
                        f"Invalid parameter cc email, the cc email({cc_email_item}) is not a mailbox"
                    )
                    return
        bcc_email = tool_parameters.get('bcc', '')
        bcc_email_list = []
        if bcc_email:
            bcc_email_list = json.loads(bcc_email)
            for bcc_email_item in bcc_email_list:
                if not email_rgx.match(bcc_email_item):
                    yield self.create_text_message(
                        f"Invalid parameter bcc email, the bcc email({bcc_email_item}) is not a mailbox"
                    )
                    return
        send_email_params = SendEmailToolParameters(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            email_account=sender,
            email_password=password,
            sender_to=receivers_email,
            subject=subject,
            email_content=email_content,
            encrypt_method=encrypt_method,
            cc_recipients=cc_email_list,
            bcc_recipients=bcc_email_list
        )
        msg = {}
        for receiver in receivers_email + cc_email_list + bcc_email_list:
            msg[receiver] = "send email success"
        result = send_mail(send_email_params)
        if result:
            for key, (integer_value, bytes_value) in result.items():
                msg[key] = f"send email failed: {integer_value} {bytes_value.decode('utf-8')}"
        yield self.create_text_message(json.dumps(msg))
