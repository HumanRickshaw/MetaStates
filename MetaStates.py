#######Packages######
from dash import Dash, html, dcc, callback, Output, Input, State, ctx, dependencies
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate as PU
from datetime import datetime
from datetime import date
import json
import math
import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype as CDT
import plotly.express as px
from urllib.request import urlopen
import webbrowser
#######End Packages######





######Constants######

#For current date graph for States.  List of all possible cumulative
#action groups.  Used in function cumulativeLegal(...).
cumulative_groups = ['Letter Only',
                     '1 Coalition Lawsuit',
                     '1 Independent Lawsuit',
                     '1 Coalition Lawsuit and Letter',
                     '1 Independent Lawsuit and Letter',
                     '2 Coalition Lawsuits',
                     '1 Coalition Lawsuit and 1 Independent Lawsuit',
                     '2 Coalition Lawsuits and Letter',
                     '1 Coalition Lawsuit, 1 Independent Lawsuit, and Letter']

#Get today's date for States for cumulative.
dt = date.today()
today = dt.strftime('%B') + ' ' + str(dt.day) + ', ' + str(dt.year)

#All date options for States.
metadates = ['May 10, 2021',
             'June 8, 2022',
             'March 28, 2023',
             'October 24, 2023',
             today]

fips_source = 'https://raw.githubusercontent.com/kjhealy/us-county/master/data/census/fips-by-state.csv'

json_source = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'

about_the_app = [dbc.Row("I used Facebook quite a bit to keep up with friends, as I lived internationally from 2009 - 2019."),
                 html.Br(),
                 dbc.Row("I was also a middle and high school maths teacher from 2004 - 2019."),
                 html.Br(),
                 dbc.Row("I remember in the beginning of 2023 when Seattle Public Schools suing Meta was in the news.  I thought it was simultaneously hilarious and fitting.  I occasionally"),
                 dbc.Row("would hear or read about the 'addictive nature' of social media and in general how the mental health of kids is different than when I was growing up.  Soon enough,"),
                 dbc.Row("it is now October 24th and 41 States and DC have filed lawsuits against Meta.  I cannot remember the last time 42 States agreed on anything..."),
                 html.Br(),
                 dbc.Row("I begin to dig and try to trace back information from local news sources.  I also tried to sniff out legal documents.  Meta has been sued an ridiculous number of"),
                 dbc.Row("for a ridiculous number of reasons.  All documents and news are specifically related to childhood addiction of social media and mental health."),
                 html.Br(),
                 dbc.Row("Making choropleth maps is one of my favorite analysis and visualization tasks, so I took it upon myself to dig deep, get dates, and make a map."),
                 dbc.Row("This class has helped me make it interactive in the way that I envisioned.")]

last_modified = [html.Br(), html.Br(), html.Br(), html.Br(),
                 'This page was last modified by Rohan Lewis on ' + today + ' at ' + str(datetime.now().time())[0:8] + '.']

ftnt1 = [html.Div("Guam, Northern Mariana Islands, and Puerto Rico signed this letter as well.")]

ftnt2 = [html.Div("Guam, Northern Mariana Islands, and Puerto Rico have only signed a letter."),
         html.Br(),
         html.Div("American Samoa and US Virgin Islands have not yet taken any action.")]

ftnt3 = [html.Div("Many states have school districts by county."),
         html.Br(),
         html.Div("This is not always the case."),
         html.Br(),
         html.Div("Sometimes cities have their own school district.  Sometimes multiple school districts are within a county.  Sometimes a school district will cross over two or more counties."),
         html.Br(),
         html.Div("To keep things simple with geojson, I took the liberty of coloring an entire county (or equivalent) if at least one school district, at least partially residing in the county, had sued Meta.")]

bold = ['#fabebe', '#46f0f0', '#fffac8', 
        '#911eb4', '#f58231', '#4363d8', 
        '#3cb44b', '#000075', '#9a6324']
######End Constants######





######Helper Functions######

#History of Meta actions for a state from df.
#Returns a cumulative group for each state.
def cumulativeLegal(df, s) :
    
    #list of actions
    ll = sorted(df[(df.State == s) & (df.Descriptor != 'Media')]['Descriptor'].tolist())
    
    if ll == ['Letter'] :
        cl = cumulative_groups[0]
    elif ll == ['Coalition Lawsuit'] :
        cl = cumulative_groups[1]
    elif ll == ['Independent Lawsuit'] :
        cl = cumulative_groups[2] 
    elif ll == ['Coalition Lawsuit', 'Letter'] :
        cl = cumulative_groups[3]
    elif ll == ['Independent Lawsuit', 'Letter'] :
        cl = cumulative_groups[4]
    elif ll == ['Coalition Lawsuit', 'Coalition Lawsuit'] :
        cl = cumulative_groups[5]
    elif ll == ['Coalition Lawsuit', 'Independent Lawsuit'] :
        cl = cumulative_groups[6]
    elif ll == ['Coalition Lawsuit', 'Coalition Lawsuit', 'Letter'] :
        cl = cumulative_groups[7]
    elif ll == ['Coalition Lawsuit', 'Independent Lawsuit', 'Letter'] :
        cl = cumulative_groups[8]
        
    return(cl)

#Update the df to graph by date and link reference.
#If a 'Media' link, shorten it.
#For states and counties.
def filterDF(df, geo, date, lref) :

    if geo == "States" :
        df = df[df.Date == date]
    if geo == "Counties" :
        df = df[df.NumericDate >= date]

    if lref == 'Media' :
        df = df[df.Descriptor == "Media"]
        print(df)
        df.Link_Name = df.Link_Name.apply(lambda x: x if x == " " else x[0:50] + ". . .")
    else :
        df = df[df.Descriptor != "Media"]
        
    return(df)
######End Helper Functions######





######STATE DF######
# Incorporate data
dfs = pd.read_csv('MetaStates.csv', encoding = "Latin-1")

#Categorize the five dates by their order.
dfs['Date'] = pd.Categorical(dfs['Date'], categories = metadates, ordered = True)

#Get Cumulative groups.  For current date graph.
for s in np.unique(dfs.State) :
    a = np.unique((dfs[dfs.State == s]['Abbreviation']))[0]
    cl = cumulativeLegal(dfs, s)
    dfs.loc[len(dfs)] = [s, a, today, '', s, 'Media', cl]
    dfs.loc[len(dfs)] = [s, a, today, '', s, 'Legal', cl]
######STATE DF######





######COUNTY DF######
#Merge on State and County for FIPS for graph.
dfc = pd.read_csv('MetaCounties.csv', encoding = "Latin-1")
fips = pd.read_csv(fips_source, encoding = "Latin-1")
with urlopen(json_source) as response:
    counties = json.load(response)
fips = fips.rename(columns = {'fips': 'FIPS',
                              'name': 'County',
                              'state': 'State'})

dfc = pd.merge(dfc, fips, on = ['State', 'County'])
dfc.FIPS = dfc.FIPS.astype(str)
#Some FIPS start with 0, and it has been removed as int.
dfc.FIPS = dfc.FIPS.apply(lambda x: '0' + x if len(x) == 4 else x)
dfc.Date = pd.to_datetime(dfc.Date, format = '%Y-%m-%d')

#For slider.
mind = min(dfc.Date)
maxd = max(dfc.Date)
max_val = (maxd-mind).days


dfc['NumericDate'] = dfc['Date']
dfc.NumericDate = dfc.NumericDate.apply(lambda x: (x - mind).days)
dfc.Date = dfc.Date.dt.strftime('%B %d, %Y').astype(str)

label0 =  mind.strftime('%B %d, %Y')
label1 = (mind + pd.Timedelta(days = max_val/3)).strftime('%B %d, %Y')
label2 = (maxd - pd.Timedelta(days = max_val/3)).strftime('%B %d, %Y')
label3 = maxd.strftime('%B %d, %Y')

marks = {0 : {'label' : label0,
              'style' : {'margin-right' : 0,
                         'width': '100px'}},
         max_val : {'label' : label3,
                    'style' : {'margin-left' : 0,
                               'width': '100px'}}}
######COUNTY DF######





######Initialize the App######
app = Dash(__name__,
           external_stylesheets = [dbc.themes.GRID],
           suppress_callback_exceptions = True)

#App layout
app.layout = dbc.Container([dbc.Row([dbc.Col([html.Div(children = 'United States v. Meta, 2021 - Present',
                                                       style = {'textAlign' : 'center',
                                                                'fontSize': 30})], width = 12)]),
                            
                            dbc.Row([html.Br()]),
                            
                            dbc.Row([dbc.Col([html.Button('About',
                                                          id = 'aboutb',
                                                          n_clicks = 0)], width = 1),
                                     
                                     dbc.Col([html.Div('Politicial Division :  ',  
                                                       style = {'textAlign' : 'right',
                                                                'margin-top' : 8,
                                                                'fontSize': 18})], width = 5),
                                     
                                     dbc.Col([dcc.RadioItems(id = 'geo',
                                                             options = ['Counties', 'States'],
                                                             value = 'States',
                                                             style = {'fontSize': 18,
                                                                      'margin-left' : 'auto',
                                                                      'margin-right' : 0,
                                                                      'width': '200px'})], width = 1),
                                     
                                     dbc.Col(width = 5)]),
                            
                            dbc.Row([html.Br()]),
                            
                            dbc.Row([dbc.Col(id = 'aboutt',
                                              children = about_the_app,
                                              style = {'display': 'none'})]),
                             
                            dbc.Row([html.Br()]),
                            dbc.Row([html.Br()]),
                            
                            dbc.Row([html.Br()]),
                            dbc.Row([html.Br()]),
                            
                            dbc.Row(id = 'select'),
                            dbc.Row([html.Br()]),
                            dbc.Row([html.Br()]),
                            dbc.Row([dbc.Col([dcc.Graph(id = 'graph1')], width = 9),          
                                     
                                     dbc.Col([#Shift footnote a little down the side of graph.
                                              html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(),
                                              html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(),
                                              html.Div(id = "footnote",
                                                       style = {'textAlign': 'left',
                                                                'fontSize': 18})], width = 3)]),
                            
                            dbc.Row(children = last_modified,
                                    style = {'textAlign': 'left',
                                             'fontSize': 18} )], fluid = True)

#About.
@callback(Output('aboutt', 'style'),
          Input('aboutb', 'n_clicks'))
def show(clicks) :
    if clicks % 2 == 1 :
        return {'display': 'block'}
    else :
        return {'display': 'none'}

#Once geo is chosen, setup date (different) and links (same).
@callback(Output('select', 'children'),
          Input('geo', 'value'))
def geoSelect(geo) :
    
    if geo == 'States' :
        
        date_input = [dbc.Col([html.Div('Select Date of Action:  ',
                                      style = {'textAlign' : 'right',
                                               'fontSize': 18})], width = 1),
                      
                      dbc.Col([dcc.Dropdown(id = 'date',
                                            options = metadates,
                                            value = metadates[3],
                                            style = {'margin-left' : 'auto',
                                                     'margin-right' : 'auto',
                                                     'width': '200px'})], width = 3)]   
    else :
        
        date_input = [dbc.Col([html.Div('Select Earliest Date:  ',
                                        style = {'textAlign' : 'right',
                                                 'fontSize': 18})], width = 1),
                      dbc.Col([dcc.Slider(id = 'date',
                                          min = 0,
                                          max = max_val,
                                          value = 0,
                                          marks = marks,
                                          included = False)], width = 3)] 
    
    children = date_input + [dbc.Col([html.Div('Select External Links :  ',  
                                               style = {'textAlign' : 'right',
                                                        'fontSize' : 18})], width = 1),
                             
                             dbc.Col([dcc.RadioItems(id = 'linkref',
                                                     options = ['Complaints, Letters, Lawsuits...',
                                                                'Media'],
                                                     value = 'Media',
                                                     style = {'fontSize': 18,
                                                              'margin-left' : 'auto',
                                                              'margin-right' : 0,
                                                              'width': '300px'})], width = 2),
                             dbc.Col(width = 5)]
   
    return(children)





@callback(Output('graph1', 'figure'),
          Output('footnote', 'children'),
          Input('date', 'value'),
          Input('linkref', 'value'),
          Input('graph1', 'clickData'),
          State('geo', 'value'))
def updateOutput(date, lref, clickData, geo):    
        
    if geo == 'States' :
        idx = 0
        lfs = 18
        ftnt = ""
        
        #Customize colors footnote.
        if date ==  metadates[0] :
            colors = [bold[0]]
            ftnt = ftnt1   
        elif date ==  metadates[1] :
            colors = [bold[1]]
        elif date ==  metadates[2] :
            colors = [bold[2]]
        elif date ==  metadates[3] :
            colors = [bold[2], bold[1]]
        elif date == metadates[4] :
            colors = bold.copy()
            lfs = 14
            ftnt = ftnt2

        #Drill down by date and link.
        dff = filterDF(dfs, geo, date, lref)

        fig = px.choropleth(data_frame = dff,
                            locations = 'Abbreviation',
                            locationmode = "USA-states",
                            category_orders = {"Group": cumulative_groups},
                            color = 'Group',
                            color_discrete_sequence = colors,
                            hover_name = 'Link_Name',
                            hover_data = {'Group' : False,
                                          'Abbreviation' : False},
                            custom_data = ['Link'])
              
        fig.update_layout(title = None,
                          legend = {'entrywidth' : 0.33,
                                    'entrywidthmode' : 'fraction',
                                    'title' : None,
                                    'font' : {'size' : lfs},
                                    'orientation' : 'h',
                                    'x' : 0.5,
                                    'y' : -0.05,
                                    'xanchor' : 'center',
                                    'yanchor' : 'middle'},
                          height = 700,
                          geo_scope = "usa",
                          margin = {'l' : 0, 't' : 0, 'r' : 0, 'b' : 70}) 
     ######End Visualize by States###### 





    ######Visualize by Counties######     
    else :
        idx = 4
        ftnt = ftnt3
        #Drill down by date and link.
        dff = filterDF(dfc, geo, date, lref)

        fig = px.choropleth(data_frame = dff,
                            geojson = counties,
                            locations = 'FIPS',
                            scope = "usa",
                            color = 'NumericDate',
                            color_continuous_scale = "Viridis_r",
                            custom_data = ['County', 'State', 'Date', 'Link_Name', 'Link'])
        
        fig.update_traces(hovertemplate = "".join(["<b>%{customdata[0]}</b>, ",
                                                   "<b>%{customdata[1]}</b>",
                                                   "<br><br>",
                                                   "<b>%{customdata[2]}</b> : ",
                                                   "<br>",
                                                   "%{customdata[3]}"])) 
        
        fig.update_layout( margin = {"r" : 0, "t" : 0, "l" : 0, "b" : 0})
        
        fig.update_coloraxes(colorbar_title_text = 'Date of <br> Action',
                             colorbar_title_font_size = 20,
                             colorbar_xpad = 20,
                             colorbar_thickness = 75,
                             colorbar_tickfont_size = 16,
                             colorbar_tickvals = [0, max_val/3, 2*max_val/3, max_val],
                             colorbar_ticktext = [label0, label1, label2, label3])
       
    #Open URL if the map gets clicked.
    if ctx.triggered_id == 'graph1' :
       url = clickData["points"][0]["customdata"][idx]
       webbrowser.open_new_tab(url)

    return(fig, ftnt)
    ######End Visualize by Counties######   

# Run the app.
if __name__ == '__main__':
    app.run(debug = True)