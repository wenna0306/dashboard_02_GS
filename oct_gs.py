import openpyxl
import pandas as pd
import plotly.graph_objects as go
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.backends.backend_agg import RendererAgg
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
matplotlib.use('agg')

_lock = RendererAgg.lock

# ------set page layout------
st.set_page_config(page_title='iSMM Dashboard',
                   page_icon = ':chart_with_upwards_trend:',
                   layout='wide',
                   initial_sidebar_state='collapsed')

cols = ['Fault Number', 'Building Trade', 'Trade Category',
        'Type of Fault', 'Impact', 'Location', 'Cancel Status', 'Reported Date',
        'Fault Acknowledged Date', 'Responded on Site Date', 'RA Conducted Date',
        'Work Started Date', 'Work Completed Date',
        'Other Trades Required Date', 'Cost Cap Exceed Date',
        'Assistance Requested Date', 'Fault Reference',
        'End User Priority', 'Incident Report', 'Remarks']

parse_dates = ['Reported Date',
                   'Fault Acknowledged Date', 'Responded on Site Date', 'RA Conducted Date',
                   'Work Started Date', 'Work Completed Date',
                   'Other Trades Required Date', 'Cost Cap Exceed Date',
                   'Assistance Requested Date']
df = pd.read_excel('Fault_Oct_2021.xlsx', header =1, index_col='Fault Number', usecols=cols, parse_dates=parse_dates)

df.columns = df.columns.str.replace(' ', '_')

df['Time_Acknowledged_mins'] = (df.Fault_Acknowledged_Date - df.Reported_Date)/pd.Timedelta(minutes=1)
df['Time_Site_Reached_mins'] = (df.Responded_on_Site_Date - df.Reported_Date)/pd.Timedelta(minutes=1)
df['Time_Work_Started_mins'] = (df.Work_Started_Date - df.Reported_Date)/pd.Timedelta(minutes=1)
df['Time_Work_Recovered_mins'] = (df.Work_Completed_Date - df.Reported_Date)/pd.Timedelta(minutes=1)

df1 = df.Location.str.split(pat=' > ', expand=True, n=4).rename(columns={0:'Site', 1:'Building', 2:'Level', 3:'Room'})

df2 = pd.concat([df, df1], axis=1)

# df_s = pd.read_excel('schedules_Oct_2021.xlsx', index_col='Schedule ID', parse_dates=['Work Started Date', 'Work Completed Date'])

# ------Sidebar------
st.sidebar.header('Please Filter Here:')

Building_Trade = st.sidebar.multiselect(
    'Select the Building Trade:',
    options=df2['Building_Trade'].unique(),
    default=df2['Building_Trade'].unique()
)

Trade_Category = st.sidebar.multiselect(
    'Select the Trade Category:',
    options=df2['Trade_Category'].unique(),
    default=df2['Trade_Category'].unique()
)

df2 = df2.query(
    'Building_Trade ==@Building_Trade & Trade_Category==@Trade_Category'
)
# st.dataframe(df_selection)

# ------Main Page------
st.title(':bar_chart:Dashboard Fault Oct 2021')
st.markdown(
    'Welcome to this Analysis App. This is the web app for Fault module on Oct 2021, get more detail from :point_right: [iSMM](https://ismm.sg/ce/login)')
st.markdown('##')

# ------Top KPI's------
total_fault = df2.shape[0]
fault_cancelled = int(df2['Cancel_Status'].notna().sum())
fault_not_recovered = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].isna()),:].shape[0]
fault_recovered = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].notna()),:].shape[0]

column01, column02, column03, column04 = st.columns(4)

with column01, _lock:
    st.subheader('**Total**')
    st.markdown(f"<h2 style='text-align: left; color: #703bef;'>{total_fault}</h2>", unsafe_allow_html=True)

with column02, _lock:
    st.subheader('Cancelled')
    st.markdown(f"<h2 style='text-align: left; color: #3c9992;'>{fault_cancelled}</h2>", unsafe_allow_html=True)

with column03, _lock:
    st.subheader('Outstanding')
    st.markdown(f"<h2 style='text-align: left; color: red;'>{fault_not_recovered}</h2>", unsafe_allow_html=True)

with column04, _lock:
    st.subheader('Recovered')
    st.markdown(f"<h2 style='text-align: left; color: #4da409;'>{fault_recovered}</h2>", unsafe_allow_html=True)

st.markdown('---')
df3 = df2.loc[(df2['Cancel_Status'].isna()) & (df2['Work_Completed_Date'].notna()),:]
cols_drop = ['Impact', 'Cancel_Status', 'Other_Trades_Required_Date', 'Cost_Cap_Exceed_Date', 'Assistance_Requested_Date',
             'Fault_Reference', 'End_User_Priority', 'Incident_Report', 'Location', 'Reported_Date', 'Fault_Acknowledged_Date',
             'Responded_on_Site_Date', 'RA_Conducted_Date', 'Work_Started_Date', 'Work_Completed_Date']
df3.drop(columns=cols_drop, inplace=True)
df3 = df3[['Site', 'Building', 'Level', 'Room', 'Building_Trade', 'Trade_Category', 'Type_of_Fault', 'Time_Acknowledged_mins',
           'Time_Site_Reached_mins', 'Time_Work_Started_mins', 'Time_Work_Recovered_mins']]
bin = [0, 10, 30, 60, np.inf]
label = ['0-10mins', '10-30mins', '30-60mins', '60-np.inf']
df3['KPI_For_Responded'] = pd.cut(df3.Time_Acknowledged_mins, bins=bin, labels=label, include_lowest=True)
df3['KPI_For_Recovered'] = pd.cut(df3.Time_Work_Recovered_mins, bins=bin, labels=label, include_lowest=True)


st.subheader('KPI Monitoring')
space01, dataframe01, space02, dataframe02, space03 = st.columns((.1, 1, .1, 1, .1))
with dataframe01, _lock:
    st.markdown('KPI vs Building Trade')
    st.dataframe(df3.groupby(by='KPI_For_Responded').Building_Trade.value_counts().unstack(level=-1).fillna(0).astype(int).style.highlight_max(
        axis=0, props='color:white; font-weight:bold; background-color:darkblue;'))

with dataframe02, _lock:
    st.markdown('KPI vs Trade Category')
    st.dataframe(df3.groupby(by='KPI_For_Responded').Trade_Category.value_counts().unstack(level=0).T.fillna(0).astype(int).style.highlight_max(
        axis=0, props='color:white; font-weight:bold; background-color:darkblue;'))

st.markdown('---')
st.subheader('Resource Allocation/Performance Monitoring Based on Building Trade-Tier 1')

df3['Time_Acknowledged_hrs'] = df3.Time_Acknowledged_mins/60
df3['Time_Site_Reached_hrs'] = df3.Time_Site_Reached_mins/60
df3['Time_Work_Started_hrs'] = df3.Time_Work_Started_mins/60
df3['Time_Work_Recovered_hrs'] = df3.Time_Work_Recovered_mins/60

df4 = df3.loc[:, ['Site', 'Building', 'Level', 'Room', 'Building_Trade', 'Trade_Category', 'Type_of_Fault', 'KPI_For_Responded',
                 'KPI_For_Recovered', 'Time_Acknowledged_hrs', 'Time_Site_Reached_hrs', 'Time_Work_Started_hrs',
                 'Time_Work_Recovered_hrs']]
df4= df4[['Site', 'Building', 'Level', 'Room', 'Building_Trade', 'Trade_Category', 'Type_of_Fault', 'Time_Acknowledged_hrs',
          'Time_Site_Reached_hrs', 'Time_Work_Started_hrs', 'Time_Work_Recovered_hrs']]

df5 = df4.groupby(by=['Building_Trade']).agg(['count', 'max', 'min', 'mean', 'sum']).sort_values((     'Time_Acknowledged_hrs', 'count'), ascending=False)
cols_name = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)', 'Fault_Acknowledged_mean(hrs)',
               'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)', 'Fault_Site_Reached_min(hrs)',
               'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count', 'Fault_Work_Started_max(hrs)',
               'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)', 'Fault_Recovered_count',
               'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']
df5.columns = cols_name
df6 = df5.loc[:, ['Fault_Acknowledged_count', 'Fault_Acknowledged_mean(hrs)', 'Fault_Acknowledged_sum(hrs)',
              'Fault_Recovered_count', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']]
df6.reset_index(inplace=True)

x = df6['Building_Trade']
y1 = df6.Fault_Acknowledged_count
y2 = df6['Fault_Acknowledged_mean(hrs)']
y3 = df6['Fault_Acknowledged_sum(hrs)']
y4 = df6.Fault_Recovered_count
y5 = df6['Fault_Recovered_mean(hrs)']
y6 = df6['Fault_Recovered_sum(hrs)']

fig01, fig02, fig03 = st.columns(3)
with fig01, _lock:
    fig01 = go.Figure(data=[go.Pie(values=y1, labels=x, hoverinfo='all', textinfo='label+percent+value', textfont_size=10, textfont_color='white', textposition='inside', showlegend=False)])
    fig01.update_layout(title='Proportions of Building Trade(Acknowledged)')
    st.plotly_chart(fig01, use_container_width=True)

with fig02, _lock:
    fig02 = go.Figure(data=[go.Bar(x=x, y=y2, orientation='v', text=y2)])
    fig02.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color='#f8481c', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig02.update_yaxes(title_text='Mean Time Spent', title_font_color='#f8481c', showgrid=True, gridwidth=0.1, gridcolor='#1f3b4d',
                       showline=True, linewidth=1, linecolor='#59656d')
    fig02.update_traces(marker_color='#f8481c', marker_line_color='#f8481c', marker_line_width=1)
    fig02.update_layout(title='Mean Time Spent to Acknowledged(hrs)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig02, use_container_width=True)

with fig03, _lock:
    fig03 = go.Figure(data=[go.Bar(x=x, y=y3, orientation='v', text=y3)])
    fig03.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color='#2afeb7', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig03.update_yaxes(title_text='Total Time Spent', title_font_color='#2afeb7', showgrid=True, gridwidth=0.1, gridcolor='#1f3b4d',
                       showline=True, linewidth=1, linecolor='#59656d')
    fig03.update_traces(marker_color='#2afeb7', marker_line_color='#2afeb7', marker_line_width=1)
    fig03.update_layout(title='Total Time Spent to Acknowledged(hrs)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig03, use_container_width=True)

fig04, fig05, fig06 = st.columns(3)
with fig04, _lock:
    fig04 = go.Figure(data=[go.Pie(values=y4, labels=x, hoverinfo='all', textinfo='label+percent+value', textfont_size=10, textfont_color='white', textposition='inside', showlegend=False)])
    fig04.update_layout(title='Proportions of Building Trade(Recovered)')
    st.plotly_chart(fig04, use_container_width=True)

with fig05, _lock:
    fig05 = go.Figure(data=[go.Bar(x=x, y=y5, orientation='v', text=y5)])
    fig05.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color='#ffb16d', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig05.update_yaxes(title_text='Mean Time Spent', title_font_color='#ffb16d', showgrid=True, gridwidth=0.1, gridcolor='#1f3b4d',
                       showline=True, linewidth=1, linecolor='#59656d')
    fig05.update_traces(marker_color='#ffb16d', marker_line_color='#ffb16d', marker_line_width=1)
    fig05.update_layout(title='Mean Time Spent to Recovered(hrs)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig05, use_container_width=True)

with fig06, _lock:
    fig06 = go.Figure(data=[go.Bar(x=x, y=y6, orientation='v', text=y6)])
    fig06.update_xaxes(title_text="Building Trade", tickangle=-45, title_font_color='#00ffff', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig06.update_yaxes(title_text='Total Time Spent', title_font_color='#00ffff', showgrid=True, gridwidth=0.1, gridcolor='#1f3b4d',
                       showline=True, linewidth=1, linecolor='#59656d')
    fig06.update_traces(marker_color='#00ffff', marker_line_color='#00ffff', marker_line_width=1)
    fig06.update_layout(title='Total Time Spent to Recovered(hrs)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig06, use_container_width=True)

st.markdown('---')
st.subheader('Resource Allocation/Performance Monitoring Based on Trade Category-Tier 2')

df7 = df4.groupby(by=['Trade_Category']).agg(['count', 'max', 'min', 'mean', 'sum']).sort_values((     'Time_Acknowledged_hrs', 'count'), ascending=False)
cols_name01 = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)', 'Fault_Acknowledged_mean(hrs)',
               'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)', 'Fault_Site_Reached_min(hrs)',
               'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count', 'Fault_Work_Started_max(hrs)',
               'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)', 'Fault_Recovered_count',
               'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']
df7.columns = cols_name01
df8 = df7.loc[:, ['Fault_Acknowledged_count', 'Fault_Acknowledged_mean(hrs)', 'Fault_Acknowledged_sum(hrs)',
             'Fault_Recovered_count', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']]
df8.reset_index(inplace=True)

df_fig07 = df8.loc[:, ['Trade_Category', 'Fault_Acknowledged_count']].sort_values('Fault_Acknowledged_count', ascending=False).head(10)
df_fig08 = df8.loc[:, ['Trade_Category', 'Fault_Acknowledged_mean(hrs)']].sort_values('Fault_Acknowledged_mean(hrs)', ascending=False).head(10)
df_fig09 = df8.loc[:, ['Trade_Category', 'Fault_Acknowledged_sum(hrs)']].sort_values('Fault_Acknowledged_sum(hrs)', ascending=False).head(10)
df_fig10 = df8.loc[:, ['Trade_Category', 'Fault_Recovered_count']].sort_values('Fault_Recovered_count', ascending=False).head(10)
df_fig11 = df8.loc[:, ['Trade_Category', 'Fault_Recovered_mean(hrs)']].sort_values('Fault_Recovered_mean(hrs)', ascending=False).head(10)
df_fig12 = df8.loc[:, ['Trade_Category', 'Fault_Recovered_sum(hrs)']].sort_values('Fault_Recovered_sum(hrs)', ascending=False).head(10)

x_fig07 = df_fig07.Trade_Category
y_fig07 = df_fig07['Fault_Acknowledged_count']
x_fig08 = df_fig08.Trade_Category
y_fig08 = df_fig08['Fault_Acknowledged_mean(hrs)']
x_fig09 = df_fig09.Trade_Category
y_fig09 = df_fig09['Fault_Acknowledged_sum(hrs)']

fig07, fig08, fig09 = st.columns(3)
with fig07, _lock:
    fig07 = go.Figure(data=[go.Bar(x=x_fig07, y=y_fig07, orientation='v', text=y_fig07)])
    fig07.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color='#fe86a4', showgrid=False,
                       showline=True, linewidth=1, linecolor='#59656d')
    fig07.update_yaxes(title_text='Count(Acknowledged)', title_font_color='#fe86a4', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig07.update_traces(marker_color='#fe86a4', marker_line_color='#fe86a4', marker_line_width=1)
    fig07.update_layout(title='Count(Acknowledged)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig07, use_container_width=True)

with fig08, _lock:
    fig08 = go.Figure(data=[go.Bar(x=x_fig08, y=y_fig08, orientation='v', text=y_fig08)])
    fig08.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color='#a55af4', showgrid=False,
                            showline=True, linewidth=1, linecolor='#59656d')
    fig08.update_yaxes(title_text='Mean Time Spent', title_font_color='#a55af4', showgrid=True, gridwidth=0.1,
                           gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig08.update_traces(marker_color='#a55af4', marker_line_color='#a55af4', marker_line_width=1)
    fig08.update_layout(title='Mean Time Spent to Acknowledged(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig08, use_container_width=True)

with fig09, _lock:
    fig09 = go.Figure(data=[go.Bar(x=x_fig09, y=y_fig09, orientation='v', text=y_fig09)])
    fig09.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color='#087871', showgrid=False,
                           showline=True, linewidth=1, linecolor='#59656d')
    fig09.update_yaxes(title_text='Total Time Spent', title_font_color='#087871', showgrid=True, gridwidth=0.1,
                           gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig09.update_traces(marker_color='#087871', marker_line_color='#087871', marker_line_width=1)
    fig09.update_layout(title='Total Time Spent to Acknowledged(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig09, use_container_width=True)

x_fig10 = df_fig10.Trade_Category
y_fig10 = df_fig10['Fault_Recovered_count']
x_fig11 = df_fig11.Trade_Category
y_fig11 = df_fig11['Fault_Recovered_mean(hrs)']
x_fig12 = df_fig12.Trade_Category
y_fig12 = df_fig12['Fault_Recovered_sum(hrs)']

fig10, fig11, fig12 = st.columns(3)
with fig10, _lock:
    fig10 = go.Figure(data=[go.Bar(x=x_fig10, y=y_fig10, orientation='v', text=y_fig10)])
    fig10.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color='#50a747', showgrid=False,
                           showline=True, linewidth=1, linecolor='#59656d')
    fig10.update_yaxes(title_text='Count(Recovered)', title_font_color='#50a747', showgrid=True, gridwidth=0.1,
                           gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig10.update_traces(marker_color='#50a747', marker_line_color='#50a747', marker_line_width=1)
    fig10.update_layout(title='Count(Recovered)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig10, use_container_width=True)

with fig11, _lock:
    fig11 = go.Figure(data=[go.Bar(x=x_fig11, y=y_fig11, orientation='v', text=y_fig11)])
    fig11.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color='#929901', showgrid=False,
                           showline=True, linewidth=1, linecolor='#59656d')
    fig11.update_yaxes(title_text='Mean Time Spent', title_font_color='#929901', showgrid=True, gridwidth=0.1,
                           gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig11.update_traces(marker_color='#929901', marker_line_color='#929901', marker_line_width=1)
    fig11.update_layout(title='Mean Time Spent to Recovered(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig11, use_container_width=True)

with fig12, _lock:
    fig12 = go.Figure(data=[go.Bar(x=x_fig12, y=y_fig12, orientation='v', text=y_fig12)])
    fig12.update_xaxes(title_text="Trade Category", tickangle=-45, title_font_color='#ff9408', showgrid=False,
                           showline=True, linewidth=1, linecolor='#59656d')
    fig12.update_yaxes(title_text='Total Time Spent', title_font_color='#ff9408', showgrid=True, gridwidth=0.1,
                           gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig12.update_traces(marker_color='#ff9408', marker_line_color='#ff9408', marker_line_width=1)
    fig12.update_layout(title='Total Time Spent to Recovered(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig12, use_container_width=True)

st.markdown('---')
st.subheader('Resource Allocation/Performance Monitoring Based on Type of Fault-Tier 3')

df9 = df4.groupby(by=['Type_of_Fault']).agg(['count', 'max', 'min', 'mean', 'sum']).sort_values((     'Time_Acknowledged_hrs', 'count'), ascending=False)
cols_name02 = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)', 'Fault_Acknowledged_mean(hrs)',
               'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)', 'Fault_Site_Reached_min(hrs)',
               'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count', 'Fault_Work_Started_max(hrs)',
               'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)', 'Fault_Recovered_count',
               'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']
df9.columns = cols_name02
df10 = df9.loc[:, ['Fault_Acknowledged_count', 'Fault_Acknowledged_mean(hrs)', 'Fault_Acknowledged_sum(hrs)',
             'Fault_Recovered_count', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']]
df10.reset_index(inplace=True)

df_fig13 = df10.loc[:, ['Type_of_Fault', 'Fault_Acknowledged_count']].sort_values('Fault_Acknowledged_count', ascending=False).head(10)
df_fig14 = df10.loc[:, ['Type_of_Fault', 'Fault_Acknowledged_mean(hrs)']].sort_values('Fault_Acknowledged_mean(hrs)', ascending=False).head(10)
df_fig15 = df10.loc[:, ['Type_of_Fault', 'Fault_Acknowledged_sum(hrs)']].sort_values('Fault_Acknowledged_sum(hrs)', ascending=False).head(10)
df_fig16 = df10.loc[:, ['Type_of_Fault', 'Fault_Recovered_count']].sort_values('Fault_Recovered_count', ascending=False).head(10)
df_fig17 = df10.loc[:, ['Type_of_Fault', 'Fault_Recovered_mean(hrs)']].sort_values('Fault_Recovered_mean(hrs)', ascending=False).head(10)
df_fig18 = df10.loc[:, ['Type_of_Fault', 'Fault_Recovered_sum(hrs)']].sort_values('Fault_Recovered_sum(hrs)', ascending=False).head(10)

x_fig13 = df_fig13.Type_of_Fault
y_fig13 = df_fig13['Fault_Acknowledged_count']
x_fig14 = df_fig14.Type_of_Fault
y_fig14 = df_fig14['Fault_Acknowledged_mean(hrs)']
x_fig15 = df_fig15.Type_of_Fault
y_fig15 = df_fig15['Fault_Acknowledged_sum(hrs)']

fig13, fig14, fig15 = st.columns(3)
with fig13, _lock:
    fig13 = go.Figure(data=[go.Bar(x=x_fig13, y=y_fig13, orientation='v', text=y_fig13)])
    fig13.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color='#3778bf', showgrid=False,
                       showline=True, linewidth=1, linecolor='#59656d')
    fig13.update_yaxes(title_text='Count(Acknowledged)', title_font_color='#3778bf', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig13.update_traces(marker_color='#3778bf', marker_line_color='#3778bf', marker_line_width=1)
    fig13.update_layout(title='Count(Acknowledged)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig13, use_container_width=True)

with fig14, _lock:
    fig14 = go.Figure(data=[go.Bar(x=x_fig14, y=y_fig14, orientation='v', text=y_fig14)])
    fig14.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color='#20f986', showgrid=False,
                       showline=True, linewidth=1, linecolor='#59656d')
    fig14.update_yaxes(title_text='Mean Time Spent', title_font_color='#20f986', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig14.update_traces(marker_color='#20f986', marker_line_color='#20f986', marker_line_width=1)
    fig14.update_layout(title='Mean Time Spent to Acknowledged(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig14, use_container_width=True)

with fig15, _lock:
    fig15 = go.Figure(data=[go.Bar(x=x_fig15, y=y_fig15, orientation='v', text=y_fig15)])
    fig15.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color='#cbf85f', showgrid=False,
                       showline=True, linewidth=1, linecolor='#59656d')
    fig15.update_yaxes(title_text='Total Time Spent', title_font_color='#cbf85f', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig15.update_traces(marker_color='#cbf85f', marker_line_color='#cbf85f', marker_line_width=1)
    fig15.update_layout(title='Total Time Spent to Acknowledged(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig15, use_container_width=True)

x_fig16 = df_fig16.Type_of_Fault
y_fig16 = df_fig16['Fault_Recovered_count']
x_fig17 = df_fig17.Type_of_Fault
y_fig17 = df_fig17['Fault_Recovered_mean(hrs)']
x_fig18 = df_fig18.Type_of_Fault
y_fig18 = df_fig18['Fault_Recovered_sum(hrs)']

fig16, fig17, fig18 = st.columns(3)
with fig16, _lock:
    fig16 = go.Figure(data=[go.Bar(x=x_fig16, y=y_fig16, orientation='v', text=y_fig16)])
    fig16.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color='#a8ff04', showgrid=False,
                       showline=True, linewidth=1, linecolor='#59656d')
    fig16.update_yaxes(title_text='Count(Recovered)', title_font_color='#a8ff04', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig16.update_traces(marker_color='#a8ff04', marker_line_color='#a8ff04', marker_line_width=1)
    fig16.update_layout(title='Count(Recovered)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig16, use_container_width=True)

with fig17, _lock:
    fig17 = go.Figure(data=[go.Bar(x=x_fig17, y=y_fig17, orientation='v', text=y_fig17)])
    fig17.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color='#ff796c', showgrid=False,
                       showline=True, linewidth=1, linecolor='#59656d')
    fig17.update_yaxes(title_text='Mean Time Spent', title_font_color='#ff796c', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig17.update_traces(marker_color='#ff796c', marker_line_color='#ff796c', marker_line_width=1)
    fig17.update_layout(title='Mean Time Spent to Recovered(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig17, use_container_width=True)

with fig18, _lock:
    fig18 = go.Figure(data=[go.Bar(x=x_fig18, y=y_fig18, orientation='v', text=y_fig18)])
    fig18.update_xaxes(title_text="Type of Fault", tickangle=-45, title_font_color='#c071fe', showgrid=False,
                       showline=True, linewidth=1, linecolor='#59656d')
    fig18.update_yaxes(title_text='Total Time Spent', title_font_color='#c071fe', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig18.update_traces(marker_color='#c071fe', marker_line_color='#c071fe', marker_line_width=1)
    fig18.update_layout(title='Total Time Spent to Recovered(hrs)-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig18, use_container_width=True)

st.markdown('---')
st.subheader('Fault by Location')
ser_fig19 = df4.groupby(['Building']).Type_of_Fault.count().sort_values()

df4.Level = df4.Level.fillna('') #Replace NaN with blank/empty string
df4['New_Location'] = df4.Building+'_'+df4.Level+'_'+df4.Room
df11 = df4.groupby(by=['New_Location']).agg(['count', 'max', 'min', 'mean', 'sum'])
cols_name003 = ['Fault_Acknowledged_count', 'Fault_Acknowledged_max(hrs)', 'Fault_Acknowledged_min(hrs)', 'Fault_Acknowledged_mean(hrs)',
               'Fault_Acknowledged_sum(hrs)', 'Fault_Site_Reached_count', 'Fault_Site_Reached_max(hrs)', 'Fault_Site_Reached_min(hrs)',
               'Fault_Site_Reached_mean(hrs)', 'Fault_Site_Reached_sum(hrs)', 'Fault_Work_Started_count', 'Fault_Work_Started_max(hrs)',
               'Fault_Work_Started_min(hrs)', 'Fault_Work_Started_mean(hrs)', 'Fault_Work_Started_sum(hrs)', 'Fault_Recovered_count',
               'Fault_Recovered_max(hrs)', 'Fault_Recovered_min(hrs)', 'Fault_Recovered_mean(hrs)', 'Fault_Recovered_sum(hrs)']
df11.columns=cols_name003
ser_fig20 = df11['Fault_Recovered_count'].sort_values().tail(10)
ser_fig21 = df11['Fault_Recovered_mean(hrs)'].sort_values().tail(10)
ser_fig22 = df11['Fault_Recovered_sum(hrs)'].sort_values().tail(10)

fig19, fig20 = st.columns(2)
with fig19, _lock:
    fig19 = go.Figure(data=[go.Bar(x=ser_fig19.values, y=ser_fig19.index, orientation='h')])
    fig19.update_xaxes(title_text="Number of Fault", title_font_color='#728f02', showgrid=True,
                       gridwidth=0.1, gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig19.update_yaxes(title_text='Building', title_font_color='#728f02', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig19.update_traces(marker_color='#728f02', marker_line_color='#728f02', marker_line_width=1)
    fig19.update_layout(title='Number of Fault vs Building', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig19, use_container_width=True)

with fig20, _lock:
    fig20 = go.Figure(data=[go.Bar(x=ser_fig20.values, y=ser_fig20.index, orientation='h')])
    fig20.update_xaxes(title_text="Number of Fault", title_font_color='#516572', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig20.update_yaxes(title_text='Level', title_font_color='#516572', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig20.update_traces(marker_color='#516572', marker_line_color='#516572', marker_line_width=1)
    fig20.update_layout(title='Number of Fault vs Level-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig20, use_container_width=True)

fig21, fig22 = st.columns(2)

with fig21, _lock:
    fig21 = go.Figure(data=[go.Bar(x=ser_fig21.values, y=ser_fig21.index, orientation='h')])
    fig21.update_xaxes(title_text="Mean Time Spent", title_font_color='#efc0fe', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig21.update_yaxes(title_text='Level', title_font_color='#efc0fe', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig21.update_traces(marker_color='#efc0fe', marker_line_color='#efc0fe', marker_line_width=1)
    fig21.update_layout(title='Mean Time Spent to Recovered(hrs) vs Level-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig21, use_container_width=True)

with fig22, _lock:
    fig22 = go.Figure(data=[go.Bar(x=ser_fig22.values, y=ser_fig22.index, orientation='h')])
    fig22.update_xaxes(title_text="Total Time Spent", title_font_color='#c7ac7d', showgrid=True, gridwidth=0.1,
                       gridcolor='#1f3b4d', showline=True, linewidth=1, linecolor='#59656d')
    fig22.update_yaxes(title_text='Level', title_font_color='#c7ac7d', showgrid=False, showline=True, linewidth=1, linecolor='#59656d')
    fig22.update_traces(marker_color='#c7ac7d', marker_line_color='#c7ac7d', marker_line_width=1)
    fig22.update_layout(title='Total Time Spent to Recovered(hrs) vs Level-Top 10', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig22, use_container_width=True)

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)