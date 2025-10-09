# agentbox/utils/output_utils.py

import time

class OutputUtils:
    @staticmethod
    def strip_echo_and_prompt(full_output: str) -> str:
        """
        简单去掉回显：找到第一行命令本身，然后把它以及之前的 prompt 去掉。
        """
        lines = full_output.splitlines()
        new_lines = []
        started = False
        for line in lines:
            if not started and "__CMD_DONE__" in line:
                continue
            # 找到命令行本身，之后开始收集
            if not started and "__CMD_DONE__" not in line and line.strip() != "":
                started = True
                new_lines.append(line)
                continue  # 跳过回显行
            if started:
                if "__CMD_DONE__" in line:
                    break
            new_lines.append(line)

        if new_lines and new_lines[0].strip() == "":
            new_lines = new_lines[1:]
            
        return '\n'.join(new_lines)
