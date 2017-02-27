from io import BytesIO
from matplotlib.figure import Figure
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_agg import FigureCanvasAgg

DEF_CHART_W = 600
DEF_CHART_H = 500

MIN_CHART_W = 400
MIN_CHART_H = 300


def gen_image_from_results(result_data, width, height):
    canvas_width = width if width is not None else DEF_CHART_W
    canvas_height = height if height is not None else DEF_CHART_H

    canvas_width = max(canvas_width, MIN_CHART_W)
    canvas_height = max(canvas_height, MIN_CHART_H)

    values = [element.value for element in result_data['results']]

    max_value = max(values)
    min_value = min(values)
    value_range = max_value - min_value
    range_increment = 0.05 * abs(value_range)

    fig = Figure(figsize=(canvas_width / 100, canvas_height / 100), dpi=100)
    ax = fig.add_axes([.1, .15, .85, .75])
    ax.set_ylim(min_value - range_increment, max_value + range_increment)

    xax = range(0, len(values))
    yax = values

    ax.set_xticks(xax)
    ax.set_xticklabels([element.date.strftime('%d %b') for element in
                       result_data['results']], rotation=75)
    ax.set_title(result_data['benchmark'].name)

    if result_data['relative']:
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f%%'))

    font_sizes = [16, 16]
    dimensions = [canvas_width, canvas_height]

    for idx, value in enumerate(dimensions):
        if value < 500:
            font_sizes[idx] = 8
        elif value < 1000:
            font_sizes[idx] = 12

    if result_data['relative']:
        font_sizes[0] -= 2

    for item in ax.get_yticklabels():
        item.set_fontsize(font_sizes[0])

    for item in ax.get_xticklabels():
        item.set_fontsize(font_sizes[1])

    ax.title.set_fontsize(font_sizes[1] + 4)

    ax.scatter(xax, yax)
    ax.plot(xax, yax)

    canvas = FigureCanvasAgg(fig)
    buf = BytesIO()
    canvas.print_png(buf)
    buf_data = buf.getvalue()

    return buf_data
