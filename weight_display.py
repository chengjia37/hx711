#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711
import smbus

# I2C LCD制御用のクラス
class LCD:
    # LCD制御用の定数
    LCD_CHR = 1  # データ送信モード
    LCD_CMD = 0  # コマンド送信モード
    
    LCD_LINE_1 = 0x80  # 1行目のアドレス
    LCD_LINE_2 = 0xC0  # 2行目のアドレス
    
    LCD_BACKLIGHT = 0x08  # バックライトON
    
    ENABLE = 0b00000100  # Enable bit
    
    # タイミング定数
    E_PULSE = 0.0005
    E_DELAY = 0.0005
    
    def __init__(self, bus_num=1, addr=0x27, port=1):
        self.addr = addr
        self.bus = smbus.SMBus(bus_num)
        self.backlight_state = self.LCD_BACKLIGHT
        
        # LCDの初期化
        self.lcd_byte(0x33, self.LCD_CMD)  # 初期化
        self.lcd_byte(0x32, self.LCD_CMD)  # 初期化
        self.lcd_byte(0x06, self.LCD_CMD)  # カーソル移動方向
        self.lcd_byte(0x0C, self.LCD_CMD)  # ディスプレイON、カーソルOFF
        self.lcd_byte(0x28, self.LCD_CMD)  # 2行モード
        self.lcd_byte(0x01, self.LCD_CMD)  # ディスプレイクリア
        time.sleep(0.05)  # コマンド実行待ち
    
    def lcd_byte(self, bits, mode):
        # ビットをLCDに送信
        bits_high = mode | (bits & 0xF0) | self.backlight_state
        bits_low = mode | ((bits << 4) & 0xF0) | self.backlight_state
        
        # High bits
        self.bus.write_byte(self.addr, bits_high)
        self.lcd_toggle_enable(bits_high)
        
        # Low bits
        self.bus.write_byte(self.addr, bits_low)
        self.lcd_toggle_enable(bits_low)
    
    def lcd_toggle_enable(self, bits):
        # Enableビットを切り替えてLCDにデータを送信
        time.sleep(self.E_DELAY)
        self.bus.write_byte(self.addr, (bits | self.ENABLE))
        time.sleep(self.E_PULSE)
        self.bus.write_byte(self.addr, (bits & ~self.ENABLE))
        time.sleep(self.E_DELAY)
    
    def clear(self):
        # ディスプレイをクリア
        self.lcd_byte(0x01, self.LCD_CMD)
        time.sleep(0.05)  # コマンド実行待ち
    
    def write_string(self, message, line=1):
        # 文字列を指定した行に表示
        if line == 1:
            self.lcd_byte(self.LCD_LINE_1, self.LCD_CMD)
        else:
            self.lcd_byte(self.LCD_LINE_2, self.LCD_CMD)
        
        for i in range(min(len(message), 16)):  # 最大16文字まで
            self.lcd_byte(ord(message[i]), self.LCD_CHR)
    
    def backlight(self, state):
        # バックライトの制御
        if state:
            self.backlight_state = self.LCD_BACKLIGHT
        else:
            self.backlight_state = 0
        self.bus.write_byte(self.addr, self.backlight_state)

def cleanAndExit():
    print("クリーンアップ中...")
    GPIO.cleanup()
    print("終了します！")
    sys.exit()

def main():
    try:
        # HX711センサーの初期化 (GPIO 5, 6に接続)
        hx = HX711(5, 6)
        
        # 読み取りフォーマットの設定
        hx.set_reading_format("MSB", "MSB")
        
        # リファレンスユニットの設定
        # 注意: この値はセンサーのキャリブレーションによって異なります
        # 正確な重量を表示するには、この値を調整する必要があります
        reference_unit = 114
        hx.set_reference_unit(reference_unit)
        
        # センサーのリセットと風袋引き
        hx.reset()
        hx.tare()
        print("風袋引き完了！重量を載せてください...")
        
        # I2C LCDディスプレイの初期化
        # 注意: I2Cアドレスはデバイスによって異なる場合があります
        # 一般的なアドレスは 0x27 または 0x3F です
        # 不明な場合は、'i2cdetect -y 1' コマンドで確認できます
        lcd = LCD(bus_num=1, addr=0x27)
        
        # LCDの初期化メッセージ
        lcd.clear()
        lcd.write_string("重量計測システム", 1)
        lcd.write_string("起動中...", 2)
        time.sleep(2)
        
        print("測定開始...")
        
        while True:
            # HX711から重量を読み取る
            weight = hx.get_weight(5)
            
            # 小数点以下2桁に丸める
            weight = round(weight, 2)
            
            # コンソールに表示
            print(f"現在の重量: {weight} g")
            
            # LCDディスプレイに表示
            lcd.clear()
            lcd.write_string("現在の重量:", 1)
            lcd.write_string(f"{weight} g", 2)
            
            # センサーの電源管理
            hx.power_down()
            hx.power_up()
            
            # 1秒待機
            time.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        lcd.clear()
        lcd.write_string("システム終了", 1)
        time.sleep(1)
        lcd.clear()
        cleanAndExit()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        try:
            lcd.clear()
            lcd.write_string("エラー発生", 1)
            lcd.write_string("システム再起動", 2)
        except:
            pass
        time.sleep(2)
        cleanAndExit()

if __name__ == "__main__":
    main()
