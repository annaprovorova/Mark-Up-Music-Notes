import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mplt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import PySimpleGUI as sg
import json 

'''отрисовка картинки''' 
def draw_picture(data, i):
    data_for_plot = pd.DataFrame(json.loads(data.webgazer_data.loc[i]))
    dict_with_targets = json.loads(data.webgazer_targets.loc[i])
    mouse_coords = json.loads(data.mouse_tracking_data.loc[i])
    x = [mouse_coords[0]['x']]
    y = [mouse_coords[0]['y']]
    img_path = data.image_opt.loc[i]
    fig = fig_maker(window, data_for_plot, dict_with_targets, x, y, img_path)
    return fig


'''создание графика'''
def fig_maker(window, data, wg_targets, x, y, img_path):  # this should be called as a thread, then time.sleep() here would not freeze the GUI
    # Построение тепловой карты
    fig = mplt.figure.Figure(figsize=(12, 3), dpi=100)
    ax = fig.add_subplot(1, 1, 1)

    ax.scatter(x, y, color='red', marker='o', s=70)
    img = plt.imread(img_path)
    ax.imshow(img  , extent=[wg_targets['#target']['left'], wg_targets['#target']['right'],
                           wg_targets['#target']['bottom'], wg_targets['#target']['top']])
    ax.axes.xaxis.set_visible(False)
    ax.axes.yaxis.set_visible(False)
    window.write_event_value('-THREAD-', 'done.')
    time.sleep(1)
    return fig

'''функция для отрисовки графика, создание виджета'''
def draw_figure(canvas, figure):
   tkcanvas = FigureCanvasTkAgg(figure, canvas)
   tkcanvas.draw()
   tkcanvas.get_tk_widget().pack(side='top', fill='both', expand=1)
   return tkcanvas


'''функция для удаления старого графика'''
def delete_fig_agg(fig_agg):
   fig_agg.get_tk_widget().forget()
   plt.close('all')




if __name__ == '__main__':
    fig_agg = None
    i = 0
    data = []
    sg.theme('LightBlue2')  # это раскраска темы
    '''отрисовка формы'''
    # можно выбрать только CSV файлы
    layout = [
        [sg.Text('Выберите файл'),
         sg.In(size=(60, 1), enable_events=True, key='-FILE-'), sg.FileBrowse(file_types=(("CSV Files", "*.csv"),))],
        [sg.Text('Номер изображения', key='-TEXT-')],
        [sg.Canvas(key='-CANVAS-')],
        [sg.Button('Предыдущая', key='-PREV-', disabled=True),
         sg.Button('Следующая', key='-NEXT-', disabled=True)],
        [sg.Text('На сколько нот разница? ("-" - влево, "+" - вправо)'), sg.InputText(key='-DIFF-', size=(10, 10), disabled=False), sg.Submit('Сохранить', key='-MELODY-', disabled=True) ],
        [sg.Submit('Сохранить в файл', key='-SAVE-', disabled=True)]
    ]

    window = sg.Window('MARK UP NOTES!', layout, finalize=True, size=(1200, 550), font=('Arial', 12), resizable=True)
    window.Refresh()

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == '-FILE-':
            file = values['-FILE-']
            window['-PREV-'].update(disabled=False)
            window['-NEXT-'].update(disabled=False)
            window['-MELODY-'].update(disabled=False)
            window['-SAVE-'].update(disabled=False)
            df = pd.read_csv(file)
            data = df[df.trial_type == 'audio-button-response'][['image_opt', 'time_elapsed', 'rt', 'webgazer_data', 'webgazer_targets',  'mouse_tracking_data', 'mouse_tracking_targets']].reset_index()
            data['difference'] = np.nan
            i = 0
            window['-TEXT-'].update(f'Тест № {i + 1}')
            if fig_agg is not None:
                delete_fig_agg(fig_agg)

            fig = draw_picture(data, i)
            fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
            window.Refresh()

        if event == '-PREV-':
            if i > 0:
                i -= 1
                window['-TEXT-'].update(f'Тест № {i + 1}')
                window['-DIFF-'].update(value="")
                if fig_agg is not None:
                    delete_fig_agg(fig_agg)

                fig = draw_picture(data, i)
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                window.Refresh()
            else:
                sg.Popup('Мелодии кончились!')
        if event == '-NEXT-':
            if i < 29:
                i += 1
                window['-TEXT-'].update(f'Тест № {i + 1}')
                window['-DIFF-'].update(value="")
                if fig_agg is not None:
                    delete_fig_agg(fig_agg)

                fig = draw_picture(data, i)
                fig_agg = draw_figure(window['-CANVAS-'].TKCanvas, fig)
                window.Refresh()
            else:
                sg.Popup('Мелодии кончились!')

        if event == '-MELODY-':
            data.loc[i, 'difference'] = float(values['-DIFF-'])
            print(i, values['-DIFF-'])

        if event == '-SAVE-':
            name = values["-FILE-"].split("/")
            filename = f'размеченный_{name[-1]}'
            # data['response'] = np.nan
            data.at[0, 'response'] = df.response.iloc[-2]
            data.at[1, 'response'] = df.response.iloc[-1]
            data.to_csv(filename, index=False, sep='|', encoding='Windows-1251')
            sg.popup(f'Файл {filename} сохранён в папку')

