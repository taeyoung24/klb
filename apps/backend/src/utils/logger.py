import colorama
from datetime import datetime
import httpx
import re
import sys
from typing import Optional, Literal

from settings import DISCORD_CONSTANTS, DISCORD_LOG_WH_URL, DISCORD_REPORT_WH_URL

# colorama 초기화
colorama.init(autoreset=True)


def _convert_markdown_bold(text: str) -> str:
    # **로 감싸진 부분을 볼드체로 변환
    return re.sub(r"\*\*(.*?)\*\*", f"{colorama.Style.BRIGHT}\\1{colorama.Style.RESET_ALL}", text)


log_level_map = {
    "DEBUG": {"level": -1, "color": colorama.Fore.BLUE, "emoji": '<:warn_blue:1363337995939217590>'},
    "INFO": {"level": 0, "color": colorama.Fore.GREEN, "emoji": '<:warn_green:1363337995939217589>'},
    "SUCCESS": {"level": 0, "color": colorama.Fore.GREEN, "emoji": '<:warn_green:1363337995939217589>'},
    "WARNING": {"level": 1, "color": colorama.Fore.YELLOW, "emoji": '<:warn_yellow:1363338001073307729>'},
    "ERROR": {"level": 2, "color": colorama.Fore.RED, "emoji": '<:warn_orange:1363337997751419002>'},
    "CRITICAL": {"level": 3, "color": colorama.Back.RED, "emoji": '<:warn_red:1363337999386935539>'}
}


class Logger:
    def __init__(self, name: Optional[str] = None):
        self.name = name

    def log(self, content: str, log_type: str = "INFO", datestr: Optional[str]=None):
        if datestr is None: datestr = datetime.now().strftime("%y.%m.%d %H:%M:%S")
        if log_type not in log_level_map:
            self.log(f"유효하지 않은 로그 타입 사용: {log_type}", "WARNING")
            log_type = "INFO"
        
        config = log_level_map[log_type]
        reset_code = colorama.Style.RESET_ALL
        bold_code = colorama.Style.BRIGHT
        
        terminal_content = f"{bold_code}{config['color']}{log_type:>8}:   {reset_code} {datestr}   {_convert_markdown_bold(content)}\n"
        sys.stdout.write(terminal_content)
        # 에러/경고는 stderr에도 출력 (버퍼링 방지)
        if log_type in ["ERROR", "CRITICAL", "WARNING"]:
            sys.stderr.write(terminal_content)
            sys.stderr.flush()
        sys.stdout.flush()


    async def log_async(self, content: str, log_type: str = "INFO", datestr: Optional[str]=None):
        if datestr is None: datestr = datetime.now().strftime("%y.%m.%d %H:%M:%S")
        if log_type not in log_level_map:
            self.log(f"유효하지 않은 로그 타입 사용: {log_type}", "WARNING")
            log_type = "INFO"
        
        self.log(content, log_type, datestr)
        config = log_level_map[log_type]
        if self.name is None:
            discord_content = f"{config['emoji']}`[{datestr}]` {content}"
        else:
            discord_content = f"{config['emoji']}`[{datestr}]` `[{self.name}]` {content}"
            
        await self._send_discord(discord_content, important=(config['level'] >= 2))
    
    
    async def report_async(self, content: str, important: bool = False):
        await self._send_discord_report(content, important=important)


    def debug(self, content: str, datestr: Optional[str]=None):
        self.log(content, "DEBUG", datestr)

    def info(self, content: str, datestr: Optional[str]=None):
        self.log(content, "INFO", datestr)

    def success(self, content: str, datestr: Optional[str]=None):
        self.log(content, "SUCCESS", datestr)

    def warning(self, content: str, datestr: Optional[str]=None):
        self.log(content, "WARNING", datestr)
        
    def error(self, content: str, datestr: Optional[str]=None):
        self.log(content, "ERROR", datestr)
        
    def critical(self, content: str, datestr: Optional[str]=None):
        self.log(content, "CRITICAL", datestr)


    async def adebug(self, content: str, datestr: Optional[str]=None):
        await self.log_async(content, "DEBUG", datestr)

    async def ainfo(self, content: str, datestr: Optional[str]=None):
        await self.log_async(content, "INFO", datestr)

    async def asuccess(self, content: str, datestr: Optional[str]=None):
        await self.log_async(content, "SUCCESS", datestr)

    async def awarning(self, content: str, datestr: Optional[str]=None):
        await self.log_async(content, "WARNING", datestr)
        
    async def aerror(self, content: str, datestr: Optional[str]=None):
        await self.log_async(content, "ERROR", datestr)
        
    async def acritical(self, content: str, datestr: Optional[str]=None):
        await self.log_async(content, "CRITICAL", datestr)


    def _emoji_warning(self, level: int) -> str:
        'level is in 0 ~ 3 (0 is the lowest)'
        if level < 0: level = 0
        elif level > 3: level = 3
        emojis = ['<:warn_green:1363337995939217589>', '<:warn_yellow:1363338001073307729>', '<:warn_orange:1363337997751419002>', '<:warn_red:1363337999386935539>']
        return emojis[level]


    async def _send_discord(self, message: str, important: bool = False) -> None:
        if important:  message = f"<@&{DISCORD_CONSTANTS.operator_role_id}>\n{message}"
                    
        payload = {"content": message}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(DISCORD_LOG_WH_URL, json=payload)
                response.raise_for_status()
                    
        except httpx.RequestError as exc:
            self.error(f"Error sending Discord notification (network): {exc}")
                
        except httpx.HTTPStatusError as exc:
            self.error(f"Error sending Discord notification (HTTP status): {exc.response.status_code} - {exc.response.text}")


    async def _send_discord_report(self, content: str, important: bool = False) -> None:
        if important: content = f"<@&{DISCORD_CONSTANTS.ceo_role_id}>\n{content}"
        payload = {"content": content}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(DISCORD_REPORT_WH_URL, json=payload)
                response.raise_for_status()
        
        except httpx.RequestError as exc:
            self.error(f"Error sending Discord report (network): {exc}")
        
        except httpx.HTTPStatusError as exc:
            self.error(f"Error sending Discord report (HTTP status): {exc.response.status_code} - {exc.response.text}")

logger = Logger()
