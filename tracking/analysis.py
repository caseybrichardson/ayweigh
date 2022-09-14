import io

from tracking.models import *
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image


def normalize_weight(row):
    if row['units'] == 'kg':
        return row['weight'] * 2.205
    else:
        return row['weight']


def weight_stats(dataframe, contestant) -> io.BytesIO:
    """
    Function to calculate contestant's individual standing
    
    dataframe: dataframe
    contestant: name
    """
    
    #get individual contestant stats
    player = dataframe.loc[dataframe['name'].eq(contestant)]
    player = player.sort_values(by='weigh_in', ascending=True)
    player['weekly_drop'] = (player.groupby(['name'])['weight_n']
                          .diff()
                          .fillna(player['weight_n'])
                          )
    
    #aggregated weight loss/gain
    weight_agg = round(player['weekly_drop'].sum() - player['weekly_drop'].max(),2)                       
    
    #graph individual contestants stats
    plt.figure(figsize=(15, 9))
    sns.set_style("whitegrid")
    sns.pointplot(x='weigh_in', y='weight_n', data=player, estimator=np.mean, markers='*', hue='name')

    plt.xlabel('Weigh-in Date')
    plt.xticks(rotation=45)
    plt.ylabel('Weight (lbs)')

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    return img_buffer


def generate_personal_progress_report(contestant_id, channel_id) -> io.BytesIO:
    contestant = Contestant.objects.get(discord_id=contestant_id, contest__channel_id=channel_id)

    # Generate dataframe
    contestant_check_ins = []

    for contestant_check_in in ContestantCheckIn.objects.filter(contestant=contestant).all():
        contestant_check_ins.append({
            'weight': contestant_check_in.weight,
            'units': contestant_check_in.units,
            'name': contestant_check_in.contestant.name,
            'weigh_in': contestant_check_in.check_in.starting
        })

    df = pd.DataFrame(contestant_check_ins)
    
    df['weigh_in']= df['weigh_in'].astype('datetime64')
    df['weigh_in'] = df['weigh_in'].dt.date
    df.sort_values(by='weigh_in', ascending=True)
    df['weight_n'] = df.apply(normalize_weight, axis=1)
    
    # Do weigh_stats logic
    img_buffer = weight_stats(df, contestant.name)
    img_buffer.seek(0)

    # Output image
    return img_buffer


def generate_contest_progress_report(contest_id) -> Image:
    pass
