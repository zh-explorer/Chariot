from typing import Union
import requests
import os

with open(os.path.expanduser("~/token"), "rt") as fp:
    TOKEN = fp.read().strip()


def submit_flag(flag: Union[str, bytes]):
    if isinstance(flag, bytes):
        flag = flag.decode("utf-8")
    r = requests.post("https://172.20.1.1/Answerapi/sub_answer_api", data={"answer": flag, "playertoken": TOKEN},
                      verify=False, timeout=3)
    return r.text
