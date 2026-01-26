import os
import asyncio
from typing import Dict, Optional, Set
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, CommandHandler
from dotenv import load_dotenv

from backend.app.schemas.remote import JobResult, FixResult, JobType
from backend.app.core.state import (
    MACHINE_STORE, 
    JOB_QUEUE, 
    LINK_STORE, 
    ANALYSIS_STORE, 
    APPROVAL_STATES, 
    ERROR_MACHINE_MAP,
    add_job
)

load_dotenv("backend/.env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class TelegramService:
    def __init__(self):
        self.application = None
        if TOKEN:
            self.application = Application.builder().token(TOKEN).build()
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("list", self.cmd_list))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("logs", self.cmd_logs))
            self.application.add_handler(CommandHandler("link", self.cmd_link))
            self.application.add_handler(CommandHandler("link", self.cmd_link))
        else:
            print("WARNING: TELEGRAM_BOT_TOKEN not set. Notifications will not work.")

    async def start(self):
        if self.application:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

    async def stop(self):
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()

    # --- Notifications ---

    async def send_approval_request(self, error_id: str, summary: str):
        if not self.application:
            return

        APPROVAL_STATES[error_id] = "pending"
        
        analysis = ANALYSIS_STORE.get(error_id)
        cmd_count = len(analysis.commands) if analysis else 0

        keyboard = []
        
        # Row 1: Approve All | Reject
        keyboard.append([
            InlineKeyboardButton("✅ Run All", callback_data=f"approve_all:{error_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject:{error_id}"),
        ])
        
        # Row 2+: Individual Commands
        if cmd_count > 0:
            row = []
            for i in range(cmd_count):
                btn_label = f"▶️ Run #{i+1}"
                row.append(InlineKeyboardButton(btn_label, callback_data=f"run_one:{error_id}:{i}"))
                if len(row) >= 3: 
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Notify Admin (Fallback)
        admin_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        targets = set()
        if admin_chat_id:
            targets.add(int(admin_chat_id))
            
        for chat_id in targets:
            try:
                await self.application.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚨 New Error Detected\n\n{summary}\n\nPlease approve or reject the fix.",
                    reply_markup=reply_markup,
                )
            except Exception as e:
                print(f"Failed to send to {chat_id}: {e}")
    
    async def notify_job_result(self, result: JobResult):
        if not self.application:
            return
            
        status_icon = "✅" if result.success else "❌"
        output = result.output
        if len(output) > 3000:
            output = output[:3000] + "\n... (truncated)"
            
        text = f"{status_icon} Job Result ({result.job_id})\nMachine: {result.machine_id}\n\nOutput:\n{output}"
        
        # Notify Admin
        admin_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if admin_chat_id:
            try:
                await self.application.bot.send_message(chat_id=admin_chat_id, text=text)
            except Exception:
                pass

    async def notify_fix_result(self, result: FixResult):
        if not self.application:
            return
            
        status_icon = "✅" if result.success else "❌"
        log = result.log
        if len(log) > 3000:
            log = log[:3000] + "\n... (truncated)"
            
        text = f"{status_icon} Fix Execution Result ({result.error_id})\n\nLog:\n{log}"
        
        admin_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if admin_chat_id:
            try:
                await self.application.bot.send_message(chat_id=admin_chat_id, text=text)
            except Exception:
                pass

    # --- Command Handlers ---

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Welcome to AI Service Monitor!\n\n"
            "Commands:\n"
            "/list - List available machines\n"
            "/link <machine_id> - Link this chat to a machine\n"
            "/status - Check status of linked machines\n"
            "/logs <machine_id> <service> - Fetch logs\n"
            "/link <machine_id> - Link this chat to a machine\n"
            "/status - Check status of linked machines\n"
            "/logs <machine_id> <service> - Fetch logs"
        )

    async def cmd_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not MACHINE_STORE:
            await update.message.reply_text("No machines connected yet.")
            return
        msg = "Available Machines:\n"
        for mid, data in MACHINE_STORE.items():
            msg += f"- {data.hostname} (ID: `{mid}`)\n"
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if len(args) < 1:
            await update.message.reply_text("Usage: /link <machine_id>")
            return
        
        machine_id = args[0]
        chat_id = update.effective_chat.id
        
        if machine_id not in MACHINE_STORE:
            await update.message.reply_text("Machine ID not found.")
            return
            
        if machine_id not in LINK_STORE:
            LINK_STORE[machine_id] = set()
        LINK_STORE[machine_id].add(chat_id)
        
        await update.message.reply_text(f"✅ Linked to {MACHINE_STORE[machine_id].hostname}.")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not MACHINE_STORE:
            await update.message.reply_text("No machines connected.")
            return

        msg = "Machine Status:\n"
        for mid, data in MACHINE_STORE.items():
            linked = "🔗" if mid in LINK_STORE and update.effective_chat.id in LINK_STORE[mid] else ""
            msg += f"🖥 {data.hostname} ({mid}) {linked}\n"
            msg += f"   Last Seen: {data.timestamp}\n"
            msg += f"   Services: {', '.join(data.services)}\n\n"
        await update.message.reply_text(msg)

    async def cmd_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("Usage: /logs <machine_id> <service>")
            return
            
        machine_id = args[0]
        service = args[1]
        
        try:
            job_id = add_job(machine_id, JobType.GET_LOGS, {"service": service})
            await update.message.reply_text(f"⏳ Requesting logs... (Job ID: {job_id})")
        except ValueError:
            await update.message.reply_text("Machine not found.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")



    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data
        parts = data.split(":")
        action = parts[0]
        error_id = parts[1]

        if action == "approve_all":
            APPROVAL_STATES[error_id] = "approved"
            await query.edit_message_text(text=f"✅ Fix for {error_id} APPROVED (Run All).")
            await self._queue_commands(error_id, "all")
            
        elif action == "run_one":
            index = int(parts[2])
            await query.edit_message_text(text=f"▶️ Executing Command #{index+1} for {error_id}...")
            await self._queue_commands(error_id, index)
            
        elif action == "reject":
            APPROVAL_STATES[error_id] = "rejected"
            await query.edit_message_text(text=f"❌ Fix for {error_id} REJECTED.")

    async def _queue_commands(self, error_id: str, target: str | int):
        machine_id = ERROR_MACHINE_MAP.get(error_id)
        if not machine_id:
            print(f"Error: Machine ID not found for error {error_id}")
            return

        analysis = ANALYSIS_STORE.get(error_id)
        if not analysis:
            return

        commands_to_queue = []
        if target == "all":
            commands_to_queue = analysis.commands
        elif isinstance(target, int):
            if 0 <= target < len(analysis.commands):
                commands_to_queue = [analysis.commands[target]]
        
        for cmd in commands_to_queue:
            # Send as EXEC_CMD job
            add_job(machine_id, JobType.EXEC_CMD, {"command": cmd.command})

# Singleton instance
telegram_service = TelegramService()
