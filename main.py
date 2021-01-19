import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud


def get_pushshift_data(data_type, **kwargs):
    '''
    Gets data from the pushshift api.

    data_type can be 'comment' or 'submission'
    The rest of the args are interpreted as payload.

    Read more: https://github.com/pushshift/api

    Implementation source: https://www.jcchouinard.com/how-to-use-reddit-api-with-python/
    '''

    base_url = f'https://api.pushshift.io/reddit/search/{data_type}/'
    payload = kwargs
    request = requests.get(base_url, params=payload)
    return request.json()


''' 
    Getting the data
'''
# Set up pushshift query
query = 'structural equation modeling'  # Add your query
data_type = 'comment'  # give me comments, use 'submission' to publish something
duration = '365d'  # Select the timeframe. Epoch value or Integer + 's,m,h,d' (i.e. 'second', 'minute', 'hour', 'day')
size = 500  # Maximum size of response TODO: seems to be limited to 500 by the API
sort_type = 'score'  # Sort by score (Accepted: 'score', 'num_comments', 'created_utc')
sort = 'desc'  # ascending / descending : 'asc', 'desc'

# Load data
queryData = get_pushshift_data(data_type=data_type,
                               q=query,
                               after=duration,
                               size=size,
                               sort_type=sort_type,
                               sort=sort)

# Create Pandas data frame
data = pd.DataFrame(queryData.get('data'))
data['created_utc'] = pd.to_datetime(data['created_utc'], unit='s')  # Transform time data
data['permalink'] = 'https://reddit.com' + data['permalink'].astype(str)  # Create full url from /r/..

''' 
    Example 1: Plotting aggregates
'''
# Compute total per subreddit
minCount = 2  # Minimum count for aggregate filter
topN = 10
data_subreddits = data['subreddit'].value_counts(sort=True)
data_subreddits_filtered = data_subreddits[data_subreddits >= minCount][:topN]

# Compute total per month
data['month'] = data['created_utc'].dt.month  # Add month number as a column
data_monthly = data['month'].value_counts(sort=False).sort_index()  # Aggregate by month and sort by month number
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
for i in range(1, len(month_names) + 1):  # add missing months in case of 0 comments
    if i not in data_monthly.index:
        data_monthly.at[i] = 0

# Plotting
fig, (ax_lhs, ax_rhs) = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Reddit comments containing '" + query + "'")
# Left: Total per subreddit
sns.set(style='white')
sns.barplot(ax=ax_lhs, y=data_subreddits_filtered.index, x=data_subreddits_filtered.values)
sns.despine(right=True, top=True)
ax_lhs.set_xlabel('N')
ax_lhs.set_ylabel('Subreddit r/')
# Right: Total per subreddit
sns.lineplot(ax=ax_rhs, x=month_names, y=data_monthly.values, linewidth=2.5, marker='o')
for tick in ax_rhs.get_xticklabels():  # Rotate all month labels
    tick.set_rotation(45)
ax_rhs.set_ylabel('N')
fig.tight_layout()

''' 
    Example 2: Top comment 
'''
# Select columns and first comment. (Data are already sorted)
data_comments = data[['author', 'subreddit', 'score', 'created_utc', 'body', 'permalink']].copy()
topComment = data_comments.iloc[0]

# Print with some simple formatting
print("Top comment for '" + query + "'")
print('Author: ' + topComment['author'])
print('Score: ' + str(topComment['score']))
print('Posted on (UTC): ' + str(topComment['created_utc']))
print('Link: ' + topComment['permalink'])
print("Comment:\n" + topComment['body'])

''' 
    Example 3: Word cloud
'''
# Concatenate all comments
text = " ".join(comment for comment in data['body'])

# Use the wordcloud library
wordcloud = WordCloud(max_font_size=50, max_words=100, background_color="white", colormap='viridis').generate(text)

# Plot!
fig = plt.figure()
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis("off")
fig.tight_layout()

# Show plots until they are closed
plt.show()
