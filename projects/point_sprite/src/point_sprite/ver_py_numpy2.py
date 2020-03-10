'''
ver_py_numpyとの違い

ver_py_numpyではspriteの座標をkivy側に渡す際に `tuple(numpyの配列)`という風に
通常のpython配列に変換してから渡しているのですが、ver_py_numpy2ではこの変換を無く
している。ただその結果、表示上のframe-rateは上がったものの実際のframe-rateはガクッ
と落ちてしまった。(目視で10fpsぐらい)。numpy用に設計されていないAPIに無理やりnumpy
配列を渡すのは良くないことなんだろう、おそらく。

- max_spawn_intervalが0の時はframe-rateは下がらなかった
'''

__all__ = ('animation', )
import numpy as np


class NumpyArrayWrapper(np.ndarray):
    def __bool__(self):
        return self.size > 0


async def animation(
        widget, *, canvas=None, max_sprites=1000, color='#FFFFFF',
        pointsize=1, image='', random=None, max_spawn_interval=.1,
        max_velocity_y=60):
    import asynckivy as ak
    await ak.sleep(0)
    
    if random is None:
        from random import Random
        random = Random()
    if canvas is None:
        canvas = widget.canvas.before

    visible_arr = np.zeros(max_sprites, dtype=bool)
    x_arr = np.zeros(max_sprites)
    y_arr = np.zeros(max_sprites)
    velocity_y_arr = np.zeros(max_sprites)
    output_arr = np.empty(max_sprites * 2).view(type=NumpyArrayWrapper)

    from kivy.utils import get_color_from_hex
    from kivy.graphics import Point, Color
    with canvas:
        color_inst = Color(*get_color_from_hex(color))
        point_inst = Point(pointsize=pointsize, source=image)

    async def _spawn_sprite():
        from asynckivy import sleep
        r = random
        min_x = min_y = -pointsize
        while True:
            await sleep(r.random() * max_spawn_interval)
            indices = (visible_arr == 0).nonzero()[0]
            if len(indices) == 0:
                assert not indices
                continue
            i = indices[0]
            max_x = int(widget.width + pointsize)
            max_y = widget.height + pointsize
            velocity_y = float(r.randint(1, max_velocity_y) * r.choice((1, -1)))
            velocity_y_arr[i] = velocity_y
            x_arr[i] = r.randint(min_x, max_x)
            y_arr[i] = min_y if velocity_y >= 0. else max_y
            visible_arr[i] = True

    async def _remove_sprite_if_its_outside_of_the_widget():
        from asynckivy import sleep
        logical_and = np.logical_and
        logical_or = np.logical_or
        min_y = -pointsize
        while True:
            await sleep(2)
            max_y = widget.height + pointsize
            visible_arr[
                logical_and(
                    visible_arr,
                    logical_or(
                        logical_and(
                            y_arr < min_y,
                            velocity_y_arr < 0,
                        ),
                        logical_and(
                            y_arr > max_y,
                            velocity_y_arr > 0,
                        ),
                    ),
                )
            ] = False

    async def _move_sprites():
        from asynckivy import sleep
        from time import perf_counter as get_current_time
        from itertools import compress, count, chain
        chain_from_iterable = chain.from_iterable

        last = get_current_time()
        while True:
            await sleep(0)
            current = get_current_time()
            delta = current - last
            last = current
            indices = visible_arr.nonzero()[0]
            n_visibles = len(indices)
            current_output = output_arr[:n_visibles * 2]
            y_arr[indices] += velocity_y_arr[indices] * delta
            current_output[::2] = x_arr[indices]
            current_output[1::2] = y_arr[indices]
            # 描画命令を更新
            point_inst.points = current_output
    
    try:
        coro_spawn = _spawn_sprite()
        coro_remove = _remove_sprite_if_its_outside_of_the_widget()
        coro_move = _move_sprites()
        ak.start(coro_spawn)
        ak.start(coro_remove)
        ak.start(coro_move)
        await ak.sleep_forever()
    finally:
        coro_spawn.close()
        coro_remove.close()
        coro_move.close()
        canvas.remove(point_inst)
        canvas.remove(color_inst)

