#!/usr/bin/env python3
"""
Claude CLI Stream-JSON 输出格式化工具

提供统一的 stream-json 解析和格式化显示功能
"""
import json
from typing import Optional, Tuple, List
from rich.console import Console
from rich.markdown import Markdown

# 使用 force_terminal 确保 rich 总是输出格式化内容
console = Console(force_terminal=True)


def format_stream_line(line: str) -> Optional[str]:
    """
    格式化 stream-json 输出为人类可读格式

    Args:
        line: JSON 字符串

    Returns:
        格式化后的字符串，如果不应该显示则返回 None
    """
    try:
        data = json.loads(line)
        msg_type = data.get("type", "unknown")
        subtype = data.get("subtype", "")

        # 根据 type 格式化输出
        if msg_type == "system":
            if subtype == "init":
                return f"[SYSTEM] 初始化 Claude (模型: {data.get('model', 'N/A')})"
            elif subtype in ["hook_started", "hook_response"]:
                return None  # 不显示 hook 信息
            else:
                return f"[SYSTEM] {subtype}"

        elif msg_type == "assistant":
            # 提取 assistant 的文本内容
            message = data.get("message", {})
            content_blocks = message.get("content", [])

            text_parts = []
            for block in content_blocks:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})

                    # 格式化工具调用详情
                    if tool_name == "TodoWrite":
                        todos = tool_input.get("todos", [])
                        return f"[TOOL] TodoWrite 更新 {len(todos)} 个任务"
                    elif tool_name == "Glob":
                        pattern = tool_input.get("pattern", "")
                        return f"[TOOL] Glob 搜索: {pattern}"
                    elif tool_name == "Read":
                        path = tool_input.get("file_path", "")
                        filename = path.split("/")[-1] if "/" in path else path
                        return f"[TOOL] Read 读取: {filename}"
                    elif tool_name == "Bash":
                        command = tool_input.get("command", "")
                        return f"[TOOL] Bash 执行: {command}"
                    elif tool_name == "Skill":
                        skill = tool_input.get("skill", "")
                        args = tool_input.get("args", "")
                        return f"[TOOL] Skill 调用: {skill} {args}"
                    elif tool_name == "Grep":
                        pattern = tool_input.get("pattern", "")
                        return f"[TOOL] Grep 搜索: {pattern}"
                    elif tool_name == "Write":
                        path = tool_input.get("file_path", "")
                        filename = path.split("/")[-1] if "/" in path else path
                        return f"[TOOL] Write 写入: {filename}"
                    else:
                        return f"[TOOL] 调用 {tool_name}"

            if text_parts:
                # 完整显示 ASSISTANT 的消息
                text = ''.join(text_parts).strip()
                # 打印前缀
                print("[ASSISTANT]", flush=True)
                # 使用 rich 渲染 markdown
                console.print(Markdown(text))
                return None  # 已经直接打印了，返回 None

        elif msg_type == "user":
            # 提取 user 的工具结果
            tool_results = data.get("content", [])
            if tool_results and len(tool_results) > 0:
                first_result = tool_results[0]
                if isinstance(first_result, dict):
                    if "tool_result" in first_result:
                        tool_use_id = first_result.get("tool_use_id", "")
                        # 从 tool_use_id 提取工具名称
                        if "call_" in tool_use_id:
                            tool_name = tool_use_id.split("_")[1].split("d")[0] if "d" in tool_use_id else "unknown"
                            content = first_result.get("content", "")

                            # 显示结果摘要
                            if isinstance(content, str) and len(content) > 0:
                                # 完整显示，不截断（用户需要看到完整输出）
                                return f"[RESULT] {tool_name}:\n{content}"
                            elif isinstance(content, dict) and "filenames" in content:
                                num_files = len(content.get("filenames", []))
                                return f"[RESULT] {tool_name}: 找到 {num_files} 个文件"
                            else:
                                return f"[RESULT] {tool_name}: ✓"
                        return f"[RESULT] {tool_use_id}"
            return None

        elif msg_type == "result":
            return f"\n{'='*60}\n[RESULT] ✓ 生成完成\n{'='*60}\n"

        return None  # 默认不显示

    except json.JSONDecodeError:
        return None
    except Exception:
        return None


def parse_stream_result(output_lines: List[str]) -> Optional[str]:
    """
    从 stream-json 输出中提取最终结果

    Args:
        output_lines: 输出行的列表

    Returns:
        最终结果文本，如果找不到则返回 None
    """
    for line in output_lines:
        try:
            data = json.loads(line)
            # 提取 type="result" 的最终结果
            if data.get("type") == "result":
                return data.get("result", "")
        except json.JSONDecodeError:
            continue

    return None


def stream_claude_output(process) -> Tuple[bool, str]:
    """
    实时显示 Claude CLI 的格式化输出，并捕获最终结果

    Args:
        process: subprocess.Popen 对象

    Returns:
        (success: bool, output: str|None)
        success - 命令是否成功
        output - 如果成功，返回原始输出（不含 JSON），否则返回错误信息
    """
    output_lines = []
    text_output_lines = []  # 收集非 JSON 的文本输出

    try:
        for line in process.stdout:
            output_lines.append(line)
            text_output_lines.append(line)

            # 格式化显示
            formatted = format_stream_line(line)
            if formatted:
                print(formatted, flush=True)

        # 等待进程结束
        returncode = process.wait()

        if returncode != 0:
            stderr_out = process.stderr.read()
            return False, stderr_out

        # 提取最终结果
        final_result = parse_stream_result(output_lines)

        # 如果有最终结果，返回它
        if final_result:
            return True, final_result

        # 否则返回所有非 JSON 的文本输出
        return True, ''.join(text_output_lines)

    except Exception as e:
        return False, str(e)


def run_claude_stream(cmd, env=None):
    """
    运行 Claude CLI 并实时显示格式化输出

    Args:
        cmd: 命令列表
        env: 环境变量字典 (可选)

    Returns:
        (success: bool, output: str|None)
    """
    import subprocess

    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return stream_claude_output(process)
