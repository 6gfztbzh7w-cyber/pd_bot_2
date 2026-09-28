import discord
from discord import app_commands
from discord.ext import commands
import requests
import json

# ==================== 設定項目 ====================
BOT_TOKEN = "MTUzMjQxMjg1MjYzMDE5NjI2NA.GISM_S.dqDGe0ezs9AZMzVlQeWfn01cG6CqQdv7_0f1kk"  # ★自分のBotトークンを貼り付け
GAS_WEB_URL = "https://script.google.com/macros/s/AKfycbxOvzqOPNAZ1Hr6r4VtLn9JoizCXd9XJgeZRf1Pdre-_4NSmRPoPtPYTWOO7EvLq95x/exec"  # ★GASで発行されたURL (https://script.google.com/macros/s/.../exec)
# =================================================

class Client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # ★この1行を追加！Bot起動時に「PollView」のボタンを記憶させます
        self.add_view(PollView())
        
        # スラッシュコマンドの同期
        await self.tree.sync()
bot = Client()

class PollView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # ボタンを無期限に有効化

    async def update_spreadsheet(self, interaction: discord.Interaction, action: str):
        # ⚠️ ボタンを押した直後に処理中メッセージ（defer）を送って3秒制限エラーを防止する
        await interaction.response.defer(ephemeral=True)

        discord_name = interaction.user.name  # 押した人のDiscordアカウント名（ユーザー名）

        payload = {
            "discord_name": discord_name,
            "action": action
        }

        try:
            # GASへ送信（タイムアウト15秒）
            response = requests.post(GAS_WEB_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
            res_data = response.json()

            if res_data.get("status") == "success":
                await interaction.followup.send(
                    f"✅ **{discord_name}** さんの回答を **「{action}」** としてスプレッドシートへ反映しました！", 
                    ephemeral=True
                )
            else:
                msg = res_data.get("message", "エラーが発生しました")
                await interaction.followup.send(
                    f"⚠️ スプレッドシートの更新に失敗しました: {msg}\n（B列のDiscord名がアカウント名「`{discord_name}`」と一致しているか確認してください）", 
                    ephemeral=True
                )

        except requests.exceptions.Timeout:
            await interaction.followup.send("⚠️ GAS（スプレッドシート）からの応答がタイムアウトしました。スプレッドシート側を確認してください。", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 通信エラーが発生しました: {e}", ephemeral=True)

    @discord.ui.button(label="継続", style=discord.ButtonStyle.green, custom_id="keep_btn")
    async def keep_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_spreadsheet(interaction, "継続")

    @discord.ui.button(label="退職", style=discord.ButtonStyle.danger, custom_id="retire_btn")
    async def retire_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_spreadsheet(interaction, "退職")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")


# スラッシュコマンド 「/継続アンケート」
@bot.tree.command(name="継続アンケート", description="署員の継続・退職確認アンケートパネルを設置します")
async def keisoku_poll(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 継続・退職 意思確認アンケート",
        description="該当するボタンを押して回答してください。\n回答結果は自動的に名簿スプレッドシートへ反映されます。",
        color=0x1F4E78
    )
    embed.add_field(
        name="⚠️ 注意事項", 
        value="※ボタンを押したアカウント名で名簿（B列）と自動照合されます。\n※「退職」を押した場合は自動で退職者シートへ移動します。", 
        inline=False
    )
    
    view = PollView()
    await interaction.response.send_message(embed=embed, view=view)


if __name__ == "__main__":
    bot.run(BOT_TOKEN)