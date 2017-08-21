from bokeh.plotting import figure, output_file, show
from bokeh.models import HoverTool
from bs4 import BeautifulSoup
import pandas as pd
import re

festival = 'Wacken'

gephi_svg_path = 'build/{}.svg'.format(festival)
bokeh_html_path = 'build/{}.html'.format(festival)

title = '{}-Bands 2018 and their shared Twitter-Followers'.format(festival)
legend_text = "Linewidth 1% - 39%"


with open(gephi_svg_path) as f:
    bs = BeautifulSoup(f.read(), 'lxml')


def lighten_hex(color, factor=0.9):
    def hex_to_rgb(value):
        """Return (red, green, blue) for the color given as #rrggbb."""
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def rgb_to_hex(red, green, blue):
        """Return color as #rrggbb for the given color values."""
        return '#%02x%02x%02x' % (red, green, blue)

    rgb = hex_to_rgb(color)
    rgb = [int((255-x)*factor+x) for x in rgb]
    return rgb_to_hex(*rgb)


height = 600#int(float(bs.find('svg')['height']))
width = 800#int(float(bs.find('svg')['width']))

edges = []
for path in bs.findAll('path'):
    x0, y0, cx0, cy0, cx1, cy1, x1, y1 = re.findall('-?\d+\.\d+',path['d'])
    edges.append({'source':path['class'][0], 'target':path['class'][1], 'x0':float(x0), 'y0':float(y0), 'x1':float(x1), 'y1':float(y1), 'cx0':float(cx0), 'cy0':float(cy0), 'cx1':float(cx1), 'cy1':float(cy1), 'fill':path['fill'], 'stroke':path['stroke'],'stroke_light':lighten_hex(path['stroke']), 'stroke-opacity':float(path['stroke-opacity']), 'stroke-width':float(path['stroke-width'])})
df_edges = pd.DataFrame(edges)

nodes = []
for circle in bs.findAll('circle'):
    nodes.append({'class':circle['class'][0], 'cx':float(circle['cx']), 'cy':float(circle['cy']), 'fill':circle['fill'], 'fill_light':lighten_hex(circle['fill']), 'fill-opacity':float(circle['fill-opacity']), 'r':float(circle['r']), 'stroke':circle['stroke'], 'stroke-opacity':circle['stroke-opacity'], 'stroke-width':circle['stroke-width']})
df_nodes = pd.DataFrame(nodes)

node_labels = []
for text in bs.findAll('text'):
    node_labels.append({'class':text['class'][0], 'fill':text['fill'], 'font-family':text['font-family'], 'font-size':text['font-size'], 'style':text['style'], 'x':float(text['x']), 'y':float(text['y']), 'text':text.get_text().strip().replace('_', ' ')})
df_node_labels = pd.DataFrame(node_labels)


node_dict = {}
for i, band in enumerate(df_nodes['class']):
    node_dict[band]=i

linked_nodes = {}
for i, band in enumerate(df_nodes['class']):
    l_nodes = df_edges[df_edges['source']==band]['target'].tolist()
    l_nodes.append(band)
    l_nodes = [node_dict[name] for name in list(node_dict.keys()) if name not in l_nodes]
    linked_nodes[i] = l_nodes

linked_edges = {}
for band in df_edges['source'].unique():
    ind_band = node_dict[band]
    ind = df_edges[df_edges['source']!=band]['target'].index.tolist()
    linked_edges[ind_band] = ind


n_x, n_y, n_fill, n_fill_light, n_r = (df_nodes['cx'], -df_nodes['cy'], df_nodes['fill'], df_nodes['fill_light'], df_nodes['r'])
e_x0, e_y0, e_x1, e_y1, e_cx0, e_cy0, e_cx1, e_cy1, e_line_color, e_line_color_light, e_line_width, e_source, e_target = (df_edges['x0'], -df_edges['y0'], df_edges['x1'], -df_edges['y1'], df_edges['cx0'], -df_edges['cy0'], df_edges['cx1'], -df_edges['cy1'], df_edges['stroke'], df_edges['stroke_light'], 0.5+df_edges['stroke-width'], df_edges['source'], df_edges['target'])
t_x, t_y, t_text, t_text_font_size = (df_node_labels['x'], -df_node_labels['y'], df_node_labels['text'], df_node_labels['font-size']+'pt')

hover_alpha = 1.0
no_hover_alpha = 1.0

from bokeh.plotting import figure, output_file, show
from bokeh.models import ColumnDataSource, Circle, HoverTool, CustomJS, Bezier, Legend, Text

output_file(bokeh_html_path)

# Basic plot setup
p = figure(width=width, height=height, tools="pan,wheel_zoom,save,reset", toolbar_location='above', title=title, active_scroll='wheel_zoom', active_drag='pan')
p.axis.visible = False

# Add a circle, that is visible only when selected
source_edges = ColumnDataSource({'x0':e_x0, 'y0':e_y0, 'x1':e_x1, 'y1':e_y1, 'cx0':e_cx0, 'cy0':e_cy0, 'cx1':e_cx1, 'cy1':e_cy1, 'line_color':e_line_color, 'line_color_light':e_line_color_light, 'line_width':e_line_width, 'source':e_source, 'target':e_target})
er = p.bezier(source=source_edges, x0='x0', y0='y0', x1='x1', y1='y1', cx0='cx0', cy0='cy0', cx1='cx1', cy1='cy1', line_color='line_color', line_width='line_width', line_alpha=no_hover_alpha)

source_edges_2 = ColumnDataSource({'x0':[], 'y0':[], 'x1':[], 'y1':[], 'cx0':[], 'cy0':[], 'cx1':[], 'cy1':[], 'line_color':[], 'line_color_light':[], 'line_width':[], 'source':[], 'target':[]})
plot_edge = p.bezier(source=source_edges_2, x0='x0', y0='y0', x1='x1', y1='y1', cx0='cx0', cy0='cy0', cx1='cx1', cy1='cy1', line_color='line_color_light', line_width='line_width', line_alpha=hover_alpha)


source_nodes = ColumnDataSource({'x':n_x, 'y':n_y, 'fill':n_fill, 'fill_light':n_fill_light, 'r':n_r})
cr = p.circle(source=source_nodes, x='x', y='y', fill_color='fill', fill_alpha=no_hover_alpha, line_color=None, radius='r')

source_nodes_2 = ColumnDataSource({'x':[], 'y':[], 'fill':[], 'fill_light':[], 'r':[]})
plot_circle = p.circle(source=source_nodes_2, x='x', y='y', fill_color='fill_light', fill_alpha=hover_alpha, line_color=None, radius='r')


source_texts = ColumnDataSource({'x':t_x, 'y':t_y, 'text':t_text, 'text_font_size':t_text_font_size})
tr = p.text(source=source_texts, x='x', y='y', text='text', text_font_size='text_font_size', text_alpha=no_hover_alpha, text_align='center', text_baseline='middle', text_font_style='bold', text_color='black')

source_texts_2 = ColumnDataSource({'x':[], 'y':[], 'text':[], 'text_font_size':[]})
plot_text = p.text(source=source_texts_2, x='x', y='y', text='text', text_font_size='text_font_size', text_alpha=hover_alpha, text_align='center', text_baseline='middle', text_font_style='bold', text_color='lightgrey')



# Add a hover tool, that selects the circle
code = """
var n_links = %s;
var circle_data = {'x': [], 'y': [], 'fill': [], 'fill_light': [], 'r': []};
var cdata = circle.data;
var indices = cb_data.index['1d'].indices;
for (i=0; i < indices.length; i++) {
    ind0 = indices[i];
    for (j=0; j < n_links[ind0].length; j++) {
        ind1 = n_links[ind0][j];
        circle_data['x'].push(cdata.x[ind1]);
        circle_data['y'].push(cdata.y[ind1]);
        circle_data['fill'].push(cdata.fill[ind1]);
        circle_data['fill_light'].push(cdata.fill_light[ind1]);
        circle_data['r'].push(cdata.r[ind1]);
    }
}
plot_circle.data = circle_data;

var text_data = {'x': [], 'y': [], 'text': [], 'text_font_size': []};
var tdata = text.data;
for (i=0; i < indices.length; i++) {
    ind0 = indices[i];
    for (j=0; j < n_links[ind0].length; j++) {
        ind1 = n_links[ind0][j];
        text_data['x'].push(tdata.x[ind1]);
        text_data['y'].push(tdata.y[ind1]);
        text_data['text'].push(tdata.text[ind1]);
        text_data['text_font_size'].push(tdata.text_font_size[ind1]);
    }
}
plot_text.data = text_data;

var e_links = %s;
var edge_data = {'x0':[], 'y0':[], 'x1':[], 'y1':[], 'cx0':[], 'cy0':[], 'cx1':[], 'cy1':[], 'line_color':[], 'line_color_light':[], 'line_width':[], 'source':[], 'target':[]};
var edata = edge.data;
for (i=0; i < indices.length; i++) {
    ind0 = indices[i];
    for (j=0; j < e_links[ind0].length; j++) {
        ind1 = e_links[ind0][j];
        edge_data['x0'].push(edata.x0[ind1]);
        edge_data['y0'].push(edata.y0[ind1]);
        edge_data['x1'].push(edata.x1[ind1]);
        edge_data['y1'].push(edata.y1[ind1]);
        edge_data['cx0'].push(edata.cx0[ind1]);
        edge_data['cy0'].push(edata.cy0[ind1]);
        edge_data['cx1'].push(edata.cx1[ind1]);
        edge_data['cy1'].push(edata.cy1[ind1]);
        edge_data['line_color'].push(edata.line_color[ind1]);
        edge_data['line_color_light'].push(edata.line_color_light[ind1]);
        edge_data['line_width'].push(edata.line_width[ind1]);
        edge_data['source'].push(edata.source[ind1]);
        edge_data['target'].push(edata.target[ind1]);
    }
}
plot_edge.data = edge_data;
""" % (linked_nodes, linked_edges)

callback = CustomJS(args={'plot_edge':plot_edge.data_source, 'edge':er.data_source, 'plot_circle':plot_circle.data_source, 'circle':cr.data_source, 'plot_text':plot_text.data_source, 'text':tr.data_source}, code=code)
p.add_tools(HoverTool(tooltips=None, callback=callback, renderers=[cr], mode='mouse'))



legend = Legend(items=[(legend_text, [er])])

p.add_layout(legend, 'below')

show(p)
df_edges.to_csv('build/edges.csv', index=False)