#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711

# I2C LCDディスプレイ用のライブラリをインポート
# 注意: このライブラリがインストールされていない場合は、以下のコマンドでインストールしてください:
# pip3 install RPLCD smbus2
from RPLCD.i2c import CharLCD

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
        lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
                      cols=16, rows=2, dotsize=8,
                      charmap='A00',
                      auto_linebreaks=True,
                      backlight_enabled=True)
        
        # LCDの初期化メッセージ
        lcd.clear()
        lcd.write_string("重量計測システム")
        lcd.cursor_pos = (1, 0)
        lcd.write_string("起動中...")
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
            lcd.write_string("現在の重量:")
            lcd.cursor_pos = (1, 0)
            lcd.write_string(f"{weight} g")
            
            # センサーの電源管理
            hx.power_down()
            hx.power_up()
            
            # 1秒待機
            time.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        lcd.clear()
        lcd.write_string("システム終了")
        time.sleep(1)
        lcd.clear()
        cleanAndExit()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        lcd.clear()
        lcd.write_string("エラー発生")
        lcd.cursor_pos = (1, 0)
        lcd.write_string("システム再起動")
        time.sleep(2)
        lcd.clear()
        cleanAndExit()

if __name__ == "__main__":
    main()
