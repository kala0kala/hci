# -*- coding: utf-8 -*-

from psychopy import visual, event, core
import multiprocessing as mp
import pygame as pg
import pandas as pd
import filterlib as flt
import blink as blk
#from pyOpenBCI import OpenBCIGanglion

def blinks_detector(quit_program, blink_det, blinks_num, blink,):
    def detect_blinks(sample):
        if SYMULACJA_SYGNALU:
            smp_flted = sample
        else:
            smp = sample.channels_data[0]
            smp_flted = frt.filterIIR(smp, 0)

        brt.blink_detect(smp_flted, -38000)
        if brt.new_blink:
            if brt.blinks_num == 1:
                #connected.set()
                print('CONNECTED. Speller starts detecting blinks.')
            else:
                blink_det.put(brt.blinks_num)
                blinks_num.value = brt.blinks_num
                blink.value = 1

        if quit_program.is_set():
            if not SYMULACJA_SYGNALU:
                print('Disconnect signal sent...')
                board.stop_stream()

    def draw_signal(sample):
        for event in pg.event.get():
            pass

        detect_blinks(sample)

        if not SYMULACJA_SYGNALU:
            smp = sample.channels_data[0]
            sample = frt.filterIIR(smp, 0)

        oldview = screen.copy()
        screen.fill(WHITE)
        screen.blit(oldview, toleft)

        values["all"].append(sample)
        if values["all"][0] == values["range"][0]:
            values["range"][0] = min(values["all"][1:])
            redraw_all(screen, values)
        if values["all"][0] == values["range"][1]:
            values["range"][1] = max(values["all"][1:])
            redraw_all(screen, values)
        values["all"] = values["all"][1:]

        if sample < values["range"][0]:
            values["range"][0] = sample
            redraw_all(screen, values)
        if sample > values["range"][1]:
            values["range"][1] = sample
            redraw_all(screen, values)

        zero = int(map_value(0, values["range"], RANGE))
        pg.draw.line(screen, BLACK, (WIDTH-2, zero), (WIDTH-1, zero), 1)

        sample = int(map_value(sample, values["range"], RANGE))
        pg.draw.line(screen, BLUE, (WIDTH-2, values["last"]), (WIDTH-1, sample), 3)

        pg.display.update()

        values["last"] = sample

    def map_value(x, a, b):
        return (x-a[0])*((b[1]-b[0])/(a[1]-a[0]))+b[0]

    def redraw_all(display, values):
        display.fill(WHITE)
        mapped = []
        for v in values["all"]:
            mapped.append(map_value(v, values["range"], RANGE))

        zero = int(map_value(0, values["range"], RANGE))
        pg.draw.line(screen, BLACK, (0, zero), (WIDTH-1, zero), 1)
        for i in range(len(mapped)-2):
            pg.draw.line(screen, BLUE, (i, mapped[i]), (i+1, mapped[i+1]), 3)
        pg.display.update()

####################################################
    SYMULACJA_SYGNALU = True
####################################################
    RYSOWANIE_WYKRESU = True
####################################################
    mac_adress = 'd2:b4:11:81:48:ad'
####################################################

    clock = pg.time.Clock()
    frt = flt.FltRealTime()
    brt = blk.BlinkRealTime()

    if RYSOWANIE_WYKRESU:
        WIDTH, HEIGHT = 900, 550
        RANGE = (HEIGHT-20, 20)
        WHITE = (0xff, 0xff, 0xff)
        BLACK = (0x00, 0x00, 0x00)
        BLUE = (0x00, 0x00, 0xff)

        pg.init()
        pg.display.set_caption("graph")
        screen = pg.display.set_mode((WIDTH, HEIGHT))
        screen.fill(WHITE)
        toleft = pg.Rect(-1, 0, WIDTH, HEIGHT)

        values = {
            "last": 0,
            "range": [0, 0],
            "all": [0]*WIDTH,
        }

        main_func = draw_signal
    else:
        main_func = detect_blinks

    if SYMULACJA_SYGNALU:
        df = pd.read_csv('dane_do_symulacji/data.csv')
        for sample in df['signal']:
            if quit_program.is_set():
                break
            main_func(sample)
            clock.tick(200)
        print('KONIEC SYGNAŁU')
        quit_program.set()
    else:
        board = OpenBCIGanglion(mac=mac_adress)
        board.start_stream(main_func)

if __name__ == "__main__":


    blink_det = mp.Queue()
    blink = mp.Value('i', 0)
    blinks_num = mp.Value('i', 0)
    #connected = mp.Event()
    quit_program = mp.Event()

    proc_blink_det = mp.Process(
        name='proc_',
        target=blinks_detector,
        args=(quit_program, blink_det, blinks_num, blink,)
    )

    # rozpoczęcie podprocesu
    proc_blink_det.start()
    print('subprocess started')

    ############################################
    # Poniżej należy dodać rozwinięcie programu
    ############################################

    win = visual.Window(
        size=[500, 500],
        units="pix",
        fullscr=False
    )

    while True:
        if blink.value == 1:
            print('BLINK!')
            blink.value = 0
        if 'escape' in event.getKeys():
            print('quitting')
            quit_program.set()
        if quit_program.is_set():
            break

# Zakończenie podprocesów
    proc_blink_det.join()
