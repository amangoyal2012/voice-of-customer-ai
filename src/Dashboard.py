import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set page configuration
st.set_page_config(page_title="Product Review Insights", layout="wide")

# Title and description
st.title("Product Review Insights Dashboard")
st.write("Interactive dashboard with drill-down capabilities for product review insights.")

# Function to load data
@st.cache_data
def load_data(file_path):
    try:
        data = pd.read_excel(file_path)
        # Convert date column to datetime if it's not already
        if 'Published Date' in data.columns:
            # data['Published Date'] = pd.to_datetime(data['Published Date']).dt.date
            data['Published Date'] = pd.to_datetime(
                data['Published Date'],
                format='%Y-%m-%d %H:%M:%S %Z',  # Specify your expected format here
                utc=True,
                errors='coerce'  # Convert problematic dates to NaT
            ).dt.date
        return data
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# Initialize session state for drill-down
if 'drill_down' not in st.session_state:
    st.session_state.drill_down = {
        'active': False,
        'source': None,
        'sentiment': None,
        'date_range': None
    }

def reset_drill_down():
    st.session_state.drill_down = {
        'active': False,
        'source': None,
        'sentiment': None,
        'date_range': None
    }

# File upload
uploaded_file = st.file_uploader("Upload Excel file with reviews", type=['xlsx', 'xls'])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        # Display raw data
        # st.subheader("Raw Data Preview")
        # st.dataframe(df.head())
        
        # Data cleaning and preparation
        required_columns = ['Published Date', 'Review Source', 'Review Summary', 
                          'Sentiment', 'Confidence']
        if 'Tags' in df.columns:
            required_columns.append('Tags')

        if all(col in df.columns for col in required_columns):
            # Sidebar filters
            st.sidebar.header("Filters")
            
            # Reset drill-down button
            if st.session_state.drill_down['active']:
                if st.sidebar.button("Reset Drill-Down"):
                    reset_drill_down()
            
            # Date range filter
            min_date = df['Published Date'].min()
            max_date = df['Published Date'].max()
            
            if st.session_state.drill_down['active'] and st.session_state.drill_down['date_range']:
                selected_dates = st.session_state.drill_down['date_range']
            else:
                selected_dates = st.sidebar.date_input(
                    "Select date range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Source filter
            all_sources = df['Review Source'].unique()
            
            if st.session_state.drill_down['active'] and st.session_state.drill_down['source']:
                selected_sources = [st.session_state.drill_down['source']]
            else:
                selected_sources = st.sidebar.multiselect(
                    "Select review sources",
                    options=all_sources,
                    default=all_sources
                )
            
            # Sentiment filter
            all_sentiments = df['Sentiment'].unique()
            
            if st.session_state.drill_down['active'] and st.session_state.drill_down['sentiment']:
                selected_sentiments = [st.session_state.drill_down['sentiment']]
            else:
                selected_sentiments = st.sidebar.multiselect(
                    "Select sentiments",
                    options=all_sentiments,
                    default=all_sentiments
                )
            
            # Tag filter
            tag_filter_enabled = False
            if 'Tags' in df.columns:
                tag_filter_enabled = True

            # Ensure Tags column is processed as a list
            df['Tags'] = df['Tags'].astype(str).apply(lambda x: [tag.strip() for tag in x.split(',') if tag.strip()])

            # Get all unique tags
            all_tags = sorted(set(tag for tags in df['Tags'] for tag in tags))

            selected_tags = st.sidebar.multiselect(
                "Filter by Tags (optional)",
                options=all_tags,
                default=[],
                help="Only show reviews that include at least one of the selected tags."
            )

            # Apply filters
            filtered_df = df[
                (df['Published Date'] >= selected_dates[0]) & 
                (df['Published Date'] <= selected_dates[1]) &
                (df['Review Source'].isin(selected_sources)) &
                (df['Sentiment'].isin(selected_sentiments))
            ]
            
            # Apply tag filter if enabled and tags selected
            if tag_filter_enabled and selected_tags:
                 filtered_df = filtered_df[filtered_df['Tags'].apply(lambda tags: any(tag in tags for tag in selected_tags))]

            # Show current drill-down status
            if st.session_state.drill_down['active']:
                st.info(f"Drill-down active: Source={st.session_state.drill_down['source']}, "
                       f"Sentiment={st.session_state.drill_down['sentiment']}")
            
            # Main content
            st.subheader("Review Insights")
            
            # Create tabs for different visualizations
            #, tab5 
            tab1, tab2, tab3, tab4 = st.tabs([
                "Sentiment Distribution", 
                "Sentiment Over Time", 
                "Source Insights",
                "Top Reviews"
                # "Heatmap"
            ])

            color_map = {
                'POSITIVE': '#4CAF50',  # Green
                'NEUTRAL': '#FFC107',   # Yellow
                'NEGATIVE': '#F44336'   # Red
            }
            
            # Define a color for each source
            review_source_color_map = {
                'PeerSpot': '#FF9900',  
                'TrustRadius': '#00B67A',
                'Gartner': '#4285F4',
            }

            default_color = '#CCCCCC'

            with tab1:
                # Pie chart with click events
                st.subheader("Sentiment Distribution")
                sentiment_counts = filtered_df['Sentiment'].value_counts()
                colors = [color_map[sentiment] for sentiment in sentiment_counts.index]

                fig1, ax1 = plt.subplots(figsize=(4, 4))
                ax1.pie(sentiment_counts, 
                        labels=sentiment_counts.index, 
                        autopct='%1.1f%%', 
                        startangle=90, 
                        textprops={'fontsize': 9},
                        wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
                        colors=colors)
                plt.tight_layout()
                ax1.axis('equal')
                # st.pyplot(fig1)

                col1, col2 = st.columns([3, 2])  # 3:2 width ratio
                with col1:
                    st.pyplot(fig1)
                with col2:
                    st.dataframe(sentiment_counts)
                
                # Add click functionality (simulated with selectbox)
                selected_sentiment = st.selectbox(
                    "Click on pie chart or select sentiment to drill down:",
                    options=sentiment_counts.index,
                    index=None,
                    placeholder="Select to drill down"
                )
                
                if selected_sentiment:
                    st.session_state.drill_down = {
                        'active': True,
                        'source': None,
                        'sentiment': selected_sentiment,
                        'date_range': selected_dates
                    }
                    st.rerun()
                
                # Horizontal bar chart with source drill-down
                st.subheader("Sentiment Count by Review Source")
                sentiment_by_source = pd.crosstab(filtered_df['Review Source'], 
                                                filtered_df['Sentiment'])

                # Get colors in correct order based on your data
                colors = [color_map[sentiment] for sentiment in sentiment_by_source.columns]
                
                fig2, ax2 = plt.subplots(figsize=(6, 2))
                sentiment_by_source.plot(kind='barh', stacked=True, ax=ax2, width=0.4, fontsize=6, color=colors)
                plt.xlabel("Count", fontsize=6)
                plt.ylabel("Review Source", fontsize=6)
                plt.legend(title="Sentiment", fontsize=6)
                plt.yticks(rotation=90)
                plt.tight_layout()
                st.pyplot(fig2)
                
                # Add source selection for drill-down
                selected_source = st.selectbox(
                    "Select source to drill down:",
                    options=sentiment_by_source.index,
                    index=None,
                    placeholder="Select to drill down"
                )
                
                if selected_source:
                    st.session_state.drill_down = {
                        'active': True,
                        'source': selected_source,
                        'sentiment': None,
                        'date_range': selected_dates
                    }
                    st.rerun()
            
            with tab2:
                # Sentiment over time (vertical bar chart)
                st.subheader("Sentiment Over Time")
                
                # Create a date-sentiment count dataframe
                df_time = filtered_df.copy()
                df_time['Published Date'] = pd.to_datetime(df_time['Published Date'])
                df_time['month_year'] = df_time['Published Date'].dt.to_period('M').astype(str)
                
                sentiment_over_time = pd.crosstab(df_time['month_year'], 
                                                df_time['Sentiment'])
                
                fig3, ax3 = plt.subplots(figsize=(12, 6))
                sentiment_over_time.plot(kind='bar', stacked=True, ax=ax3, color= colors)
                plt.xlabel("Month-Year", fontsize=6)
                plt.ylabel("Count", fontsize=6)
                plt.xticks(rotation=45, fontsize=5)
                plt.legend(title="Sentiment")
                st.pyplot(fig3)
                
                # Add date range selection for drill-down
                st.write("Select date range to drill down:")
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start date", min_date)
                with col2:
                    end_date = st.date_input("End date", max_date)
                
                if st.button("Apply Date Drill-Down"):
                    st.session_state.drill_down = {
                        'active': True,
                        'source': None,
                        'sentiment': None,
                        'date_range': (start_date, end_date)
                    }
                    st.rerun()
            
            with tab3:
                # Review source analysis
                st.subheader("Review Source Insights")
                
                # Count by source
                source_counts = filtered_df['Review Source'].value_counts()
                source_colors = [review_source_color_map.get(source, default_color) for source in source_counts.index]

                fig4, ax4 = plt.subplots(figsize=(6, 2))
                source_counts.plot(kind='bar', ax=ax4, width=0.4, fontsize=6,
                                    color=source_colors, edgecolor='black',  # Add borders
                                    linewidth=0.5)
                plt.xlabel("Review Source", fontsize=6)
                plt.ylabel("Number of Reviews", fontsize=6)
                plt.xticks(rotation=45, fontsize=6)
                plt.grid(axis='x', linestyle='--', alpha=0.6)
                plt.tight_layout()
                st.pyplot(fig4)
                
                # Add source selection for drill-down
                selected_source = st.selectbox(
                    "Select source to drill down from chart:",
                    options=source_counts.index,
                    index=None,
                    placeholder="Select to drill down"
                )
                
                if selected_source:
                    st.session_state.drill_down = {
                        'active': True,
                        'source': selected_source,
                        'sentiment': None,
                        'date_range': selected_dates
                    }
                    st.rerun()
                
                # Average sentiment confidence by source
                avg_confidence = filtered_df.groupby('Review Source')['Confidence'].mean().sort_values()

                fig5, ax5 = plt.subplots(figsize=(6, 2))
                avg_confidence.plot(kind='barh', color='yellow', ax=ax5, width=0.4, fontsize=6)
                plt.xlabel("Average Sentiment Confidence", fontsize=6)
                plt.ylabel("Review Source", fontsize=6)
                plt.xticks(fontsize=5)
                plt.yticks(fontsize=5)
                plt.tight_layout()
                st.pyplot(fig5)
            
            with tab4:
                # Top reviews
                st.subheader("Top Positive Reviews")
                
                # Calculate a combined score for ranking
                sentiment_weights = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
                filtered_df['sentiment_weight'] = filtered_df['Sentiment'].map(sentiment_weights)
                filtered_df['combined_score'] = filtered_df['Confidence'] * filtered_df['sentiment_weight']
                
                # Top 5 positive reviews (high confidence positive)
                top_positive = filtered_df.nlargest(5, 'combined_score')
                
                for idx, row in top_positive.iterrows():
                    with st.expander(f"Positive Review from {row['Review Source']} (Score: {row['combined_score']:.2f})"):
                      st.markdown(f"""
                      **Source:** {row['Review Source']}  
                      **Date:** {row['Published Date']}  
                      **Confidence:** {row['Confidence']:.2f}  
                      **Review:** {row['Review Summary']}  
                      """)
                      if st.button(f"Drill down to {row['Review Source']}", key=f"pos_{idx}"):
                          st.session_state.drill_down = {
                              'active': True,
                              'source': row['Review Source'],
                              'sentiment': None,
                              'date_range': selected_dates
                          }
                          st.rerun()
                
                st.subheader("Top Negative Reviews")
                
                # Top 5 negative reviews (high confidence negative)
                top_negative = filtered_df.nsmallest(5, 'combined_score')
                
                for idx, row in top_negative.iterrows():
                    with st.expander(f"Negative Review from {row['Review Source']} (Score: {row['combined_score']:.2f})"):
                        st.markdown(f"""
                        **Source:** {row['Review Source']}  
                        **Date:** {row['Published Date']}  
                        **Confidence:** {row['Confidence']:.2f}  
                        **Review:** {row['Review Summary']}  
                        """)
                        if st.button(f"Drill down to {row['Review Source']}", key=f"neg_{idx}"):
                            st.session_state.drill_down = {
                                'active': True,
                                'source': row['Review Source'],
                                'sentiment': None,
                                'date_range': selected_dates
                            }
                            st.rerun()
            
            # with tab5:
            #     # Heatmap with click events
            #     st.subheader("Sentiment Heatmap Over Time")
                
            #     # Prepare data for heatmap
            #     heatmap_data = filtered_df.copy()
            #     # heatmap_data['Published Date'] = pd.to_datetime(heatmap_data['Published Date'])
            #     heatmap_data['Published Date'] = pd.to_datetime(
            #                                           heatmap_data['Published Date'],
            #                                           format='%Y-%m-%d %H:%M:%S %Z',  # Specify your expected format here
            #                                           utc=True,
            #                                       )
            #     heatmap_data['date'] = heatmap_data['Published Date'].dt.date
            #     heatmap_data['sentiment_numeric'] = heatmap_data['Sentiment'].map(
            #         {'Positive': 1, 'Neutral': 0, 'Negative': -1}
            #     )
                
            #     # Create pivot table for heatmap
            #     pivot_table = heatmap_data.pivot_table(
            #         index='date',
            #         columns='Review Source',
            #         values='sentiment_numeric',
            #         aggfunc='mean',
            #         fill_value=0
            #     )
                
            #     fig6, ax6 = plt.subplots(figsize=(12, 8))
            #     sns.heatmap(
            #         pivot_table.T,
            #         cmap='coolwarm',
            #         center=0,
            #         annot=True,
            #         fmt=".1f",
            #         linewidths=.5,
            #         ax=ax6
            #     )
            #     plt.title("Average Sentiment by Date and Source")
            #     plt.xlabel("Date")
            #     plt.ylabel("Review Source")
            #     st.pyplot(fig6)
                
            #     # Add heatmap cell selection for drill-down
            #     st.write("Select parameters to drill down from heatmap:")
            #     col1, col2 = st.columns(2)
            #     with col1:
            #         heatmap_source = st.selectbox(
            #             "Select source:",
            #             options=pivot_table.columns,
            #             index=None,
            #             placeholder="Select source"
            #         )
            #     with col2:
            #         heatmap_date = st.selectbox(
            #             "Select date:",
            #             options=pivot_table.index.strftime('%Y-%m-%d'),
            #             index=None,
            #             placeholder="Select date"
            #         )
                
            #     if st.button("Apply Heatmap Drill-Down"):
            #         if heatmap_source and heatmap_date:
            #             selected_date = pd.to_datetime(heatmap_date).date()
            #             st.session_state.drill_down = {
            #                 'active': True,
            #                 'source': heatmap_source,
            #                 'sentiment': None,
            #                 'date_range': (selected_date, selected_date)
            #             }
            #             st.rerun()
        
        else:
            st.error("The uploaded file doesn't contain all required columns. Please check your data.")
else:
    st.info("Please upload an Excel file to get started.")