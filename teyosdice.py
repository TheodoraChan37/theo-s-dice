import discord
import dice
import math
import sys
import logging
from datetime import datetime
import json
import cv2
import numpy as np
import random
import time
from discord import app_commands


intents =discord.Intents.default()
intents.typing = False
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s] - [%(name)s]:%(message)s", filename="Teyo's dice.log")


pat = '\d{1,3}d\d{1,6}|d{1,3}D\d{1,6}'
sp_pat = 'd|D'

PATH = "./USERS.json"
TOKEN_PATH = "./TOKEN.txt"
TIME_START = {}

#{server1:{id:1,id:2},server2:{id:1,id:2}}
class Data():
    SERVERS = {}
    TIME_START = {}

    async def init(self):
        for guild in client.guilds:
            self.SERVERS[str(guild.id)] = {}
            async for member in client.get_guild(guild.id).fetch_members():
                self.SERVERS[str(guild.id)][str(member.id)] = 0
                self.TIME_START[str(member.id)] = 0
        save()
        print("data initialized")
    async def time_init(self):
        for guild in client.guilds:
            async for member in client.get_guild(guild.id).fetch_members():
                self.TIME_START[str(member.id)] = 0
        print("start time initialized")

data = Data()
#ユーザー固有データの操作
#jsonへの書き出し
def save():
    f = open(PATH, 'w')
    json.dump(data.SERVERS, f, indent=4)
    f.close()
    print("data saved")
    logging.info("data saved")

#jsonからの読み込み
def load():
    f = open(PATH, "r")
    data.SERVERS = json.load(f)
    f.close()
    print("data loaded")
    logging.info("data loaded")

#秒からH:M:Sへ変換
def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return hours, minutes, seconds

#YYYYMMDDを統一暦に変換する関数 strでエラーを含めreturn
def UC(date, user):
    date = str(date)
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]

    if int(year) <= 2008:
        logging.error(f"{user} -> BCNotSupported")
        return "紀元前には対応していません。2009年1月以降を指定してください。\n(エラー:BCNotSupported)"
    elif len(str(date)) != 8:
        logging.error(f"{user} -> InvalidNumber")
        return "入力された数値が正しくありません。8桁(yyyy/mm/dd)で入力してください。\n(エラー:InvalidIntNumber)"
    elif int(month) >= 13 or int(month) <= 0:
        logging.error(f"{user} -> InvalidMonthNumber")
        return f"正しい月を入力してください。 {month}月は存在しません。\n(エラー:InvalidMonthNumber)"
    elif int(day) >= 32 or int(day) <= 0:
        logging.error(f"{user} -> InvalidDayNumber")
        return f"正しい日を入力してください。 {day}日は存在しません。\n(エラー:InvalidDayNumber)"
    else:
        fixedY = int(year) - 2000
        resultY = ((fixedY - 9) * 12) + int(month)
        fixedD = math.floor(int(day)/2.58)
        if fixedD < 1:
            fixedD = 1
        result = f"{year}年{month}月{day}日の統一暦は{resultY}年{fixedD}月です。"
        return result

#統一暦年を現在の年月に変換する関数
def FC(date):
        fix = math.floor(2000 + (int(date) / 12) + 9)
        return f"統一暦{date}年は約{fix}年です。"

#起動時イベント、ぼくはここでアクティビティとコマンドの同期をしてるよ
@client.event
async def on_ready():
    print('[Teyos dice]login successfully done!')
    await client.change_presence(activity=discord.Game(name="nDnで動くダイスBOT by RST", type=1))
    await tree.sync()

    await data.time_init()
    load()

#コマンド追加ゾーン、descriptionのおかげでコメントいらないかも
@tree.command(name="t", description="現実の任意の年月日から統一暦に変換します。YYYYMMDD形式で入力してください。")
async def t(interaction: discord.Interaction, 日付:int):
    result = UC(日付, interaction.user)
    logging.info(f"{interaction.user.name} issued /t command")
    if "エラー" in result:
        embed = discord.Embed(title="Error", color=0xFF0000, description=result)
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=result, color=0x7fffd4)
        await interaction.response.send_message(embed=embed)

@tree.command(name="today", description="今日の日付を統一暦に変換します。")
async def today(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} issued /today command")
    embed = discord.Embed(title=UC(datetime.now().strftime('%Y%m%d'), interaction.user), color=0x7fffd4)
    await interaction.response.send_message(embed=embed)

@tree.command(name="ft", description="統一暦から現在の年月におおよそで変換します。(例：/ft 100)")
async def ft(interaction: discord.Interaction, 統一暦年:int):
    logging.info(f"{interaction.user.name} issued /ft command")
    embed = discord.Embed(title=FC(統一暦年), color=0x7fffd4)
    await interaction.response.send_message(embed=embed)

@tree.command(name="randomcolor", description="ランダムな色を生成します。")
async def rc(interaction: discord.Interaction):
    logging.info(f"{interaction.user.name} issued /randomcolor command")
    img = np.zeros((100,100,3), np.uint8)
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    h = f"#{hex(r).strip('0x')} {hex(g).strip('0x')} {hex(b).strip('0x')}"
    msg = f"R:{r} G:{g} B:{b} {h}"
    img[:,:,0:3] = [b,g,r]
    cv2.imwrite('img.png',img)
    embed = discord.Embed(title=msg)
    file= discord.File(fp="img.png",filename="img.png")
    embed.set_image(url=f"attachment://img.png")
    await interaction.response.send_message(file=file,embed=embed)

@tree.command(name="shutdown",description="Botを停止。bot管理者のみ実行できます。")
async def shutdown(interaction:discord.Interaction):
    if interaction.user.id == 140833667697082368:
        embed = discord.Embed(title="Botを停止します。",color=0x7fffd4)
        save()
        await interaction.response.send_message(embed=embed)
        await client.close()
        await sys.exit()
    else:
        embed = discord.Embed(title="Error",color=0xFF0000,description="必要な権限を持っていません。\nエラーが発生している場合はbot管理者へ直ちに報告してください。")
        await interaction.response.send_message(embed=embed)

@tree.command(name="charcount",description="文字数をカウントします。結果や送信した文字列はあなたにだけ表示されます。(文字種や改行等で多少前後します。)")
async def char(interaction: discord.Interaction, text:str):
    logging.info(f"{interaction.user.name} issued /charcount command")
    embed = discord.Embed(title="解析結果",color=0x7fffd4,description=f"{len(text)}文字です。")
    await interaction.response.send_message(embed=embed,ephemeral=True)

@tree.command(name="rank",description="VCに接続している時間をランキング形式で表示します。")
async def rank(interaction: discord.Interaction, count:int=10):
    logging.info(f"{interaction.user.name} issued /rank command")
    load()
    sort = sorted(data.SERVERS[str(interaction.guild_id)].items(), key=lambda x:x[1], reverse=True)
    value = " "
    x = 1
    for i in sort:
        if i[1] != 0:
            h,m,s = seconds_to_hms(i[1])
            value += f"{x}位：{client.get_user(int(i[0])).display_name} {h}時間{m}分{s}秒\n"
            x += 1
        if x > count:
            break
    if x == 1:
        value = "表示できるデータがありません。\n参加者全員が0秒を記録しています。"
    embed = discord.Embed(title="VC接続時間ランキング",description=value)
    await interaction.response.send_message(embed=embed)

@tree.command(name="initdic", description="管理者用の辞書初期化コマンドです。")
async def init(interaction: discord.Interaction):
    if interaction.user.id == 140833667697082368:
        await Data.init()

#VCの変化をキャッチ
@client.event
async def on_voice_state_update(member, before, after):
    if before.channel != after.channel:
        #入室
        if after.channel is not None and not after.afk:
            data.TIME_START[str(member.id)] = time.time()
            print(f"{member}が{after.channel.guild.name}のVCに参加しました。")
            logging.info(f"{member.name} joined to VC")
        #退出
        if (before.channel is not None) and (after.channel is not before.channel) and not (before.afk):
            result = int(time.time()) - int(data.TIME_START[str(member.id)])
            data.SERVERS[str(member.guild.id)][str(member.id)] += result
            print(f"{member}が{before.channel.guild.name}VCから退出しました")
            logging.info(f"{member.name} left the VC")
            save()


#ダイスだけは処理が面倒(コマンド化したらUXもひどいものになる)のでon_messageをトリガー。
@client.event
async def on_message(message):
    msg = message.content
    result = dice.nDn(msg)
    if result is not None:
        embed = discord.Embed(title="ダイス結果",color=0x7fffd4)
        embed.add_field(name=result[0], value=result[1])
        if len(result) == 3:
            embed.add_field(name="合計",value=result[2])
        await message.reply(embed=embed)
        logging.info(f"{message.author.name} issued {msg}")
    
#Twitter(旧Twitter)のサムネ表示が出来なかった時の遺骸
    # if msg.startswith("https://twitter.com"):
    #     fix = msg.replace("twitter.com", "fxtwitter.com")
    #     await message.channel.send(fix)
    #     logging.info(str(message.author)+ " shared and fixed " + msg)
    # elif msg.startswith("https://x.com"):
    #     fix = msg.replace("x.com", "fxtwitter.com")
    #     await message.channel.send(fix)
    #     logging.info(str(message.author)+ " shared and fixed " + msg)

f = open(TOKEN_PATH, 'r')
TOKEN = f.read()
f.close()

client.run(TOKEN)