import os
import numpy as np
from bokeh.models import ColumnDataSource
from bokeh.resources import INLINE
from bokeh.embed import components
from bokeh.plotting import figure
import requests as requests
from test import SearchForm
from flask import Flask
from flask import render_template, request
from flask_session import Session
import pandas as pd

app = Flask(__name__)
SESSION_TYPE = "filesystem"
PERMANENT_SESSION_LIFETIME = 1800

app.config.update(SECRET_KEY=os.urandom(24))

app.config.from_object(__name__)
Session(app)


@app.route('/', methods=['GET', 'POST'])
def main():
    z = SearchForm(request.form).search.data
    if request.method == 'POST':
        r = requests.get('http://openlibrary.org/search.json?q=' + z.replace(" ", "+"))
        return search_results(r)

    return render_template('index.html')


@app.route('/results')
def search_results(data):
    df = pd.DataFrame(data.json())
    dfd = df['docs'].to_dict()
    df2 = pd.DataFrame(dfd).T
    cols = [df2['key'], df2['title'], df2['first_publish_year'], df2['author_name'], df2['isbn']]
    df3 = pd.DataFrame(cols).T
    df3 = df3.dropna()
    ls = []
    ls2 = []
    ls3 = []
    for i in df3['isbn']:
        rf = 'https://covers.openlibrary.org/b/isbn/' + str(i[0]) + '-M.jpg'
        ls.append(rf)

    for i in df3['key']:
        var = 'https://openlibrary.org' + i
        ls2.append(var)

    for i in df3['isbn']:
        if type(i) == list:
            ls3.append(i[0])
        else:
            var2 = list(i)
            print(var2)

    df3.drop(columns='isbn', inplace=True)

    df9 = pd.DataFrame(ls3, columns=["isbn"])

    df8 = pd.DataFrame(ls2, columns=["url"])
    df4 = pd.DataFrame(ls, columns=["photo"])
    data = pd.DataFrame(list(df3['first_publish_year']), columns=["first_publish_year"])

    hist, edges = np.histogram(data, bins=10)

    df6 = pd.DataFrame({'first_publish_year': hist,
                        'left': edges[:-1],
                        'right': edges[1:]})
    df7 = pd.concat([df4, df8, df3, df9], axis=1)
    ls = []
    for i in df7['author_name']:
        if type(i) == list:
            ls.append(i[0])
        else:
            ls.append(i)

    df7.drop(columns='author_name', inplace=True)

    df7['author_name'] = ls

    df7.drop(columns='key', inplace=True
             )

    src = ColumnDataSource(df6)

    fig = figure(plot_height=600, plot_width=720, )
    fig.quad(source=src, top='first_publish_year', bottom=0, left='left', right='right', line_color="white")
    fig.yaxis.axis_label = "Total Published"
    fig.xaxis.axis_label = "First Year Published"

    script, div = components(fig)
    return render_template(
        'results.html',
        tables=[df7.to_html(table_id="data", classes="table", render_links=True)],
        titles=df7.columns.values,
        plot_script=script,
        plot_div=div,
        js_resources=INLINE.render_js(),
        css_resources=INLINE.render_css(),
    ).encode(encoding='UTF-8')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
