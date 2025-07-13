

import streamlit as st
from nselib import derivatives
import pandas as pd
import logging
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# Set up logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="NSE Premium Traded Dashboard",
    page_icon="📈",
    layout="wide"
)

def get_premium_traded_data(selected_date):
    """
    Extract the core logic from your Flask route and adapt it for Streamlit
    """
    # Convert date to the required format (dd-mm-yyyy)
    try:
        formatted_date = selected_date.strftime("%d-%m-%Y")
    except Exception as e:
        st.error(f"Date formatting error: {e}")
        return None
    
    try:
        # Fetch data using nselib
        data = derivatives.fno_bhav_copy(formatted_date)
        
        # Check if expected columns exist
        required_cols = {'OptnTp', 'TtlTradgVol', 'SttlmPric', 'NewBrdLotQty', 'TckrSymb'}
        if data.empty or not required_cols.issubset(data.columns):
            st.warning(f"Data not available or missing columns for date {formatted_date}")
            return None
        
        # Filter for PE and CE options
        filtered_data = data[data['OptnTp'].isin(['PE', 'CE'])]
        
        # Calculate Premium Traded
        filtered_data = filtered_data.copy()
        filtered_data['Premium Traded'] = (
            filtered_data['TtlTradgVol'] * filtered_data['SttlmPric'] * filtered_data['NewBrdLotQty']
        )
        
        # Group by ticker symbol and sum premium traded
        grouped_data = filtered_data.groupby('TckrSymb')['Premium Traded'].sum().reset_index()
        grouped_data = grouped_data.sort_values(by='Premium Traded', ascending=False)
        grouped_data['Premium Traded (Crores)'] = grouped_data['Premium Traded'] / 10_000_000
        
        return grouped_data[['TckrSymb', 'Premium Traded (Crores)']]
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

def main():
    # Title and description
    st.title("📈 NSE Premium Traded Dashboard")
    st.markdown("View premium traded data for NSE F&O instruments")
    
    # Sidebar for controls
    st.sidebar.header("Controls")
    
    # Date picker
    selected_date = st.sidebar.date_input(
        "Select Date",
        value=date(2025, 7, 7),
        help="Select the date for which you want to view premium traded data"
    )
    
    # Fetch data button
    if st.sidebar.button("Fetch Data", type="primary"):
        with st.spinner("Fetching data..."):
            data = get_premium_traded_data(selected_date)
            
            if data is not None and not data.empty:
                # Store data in session state
                st.session_state.data = data
                st.session_state.selected_date = selected_date
                st.success(f"Data loaded successfully for {selected_date.strftime('%d-%m-%Y')}")
            else:
                st.error("No data available for the selected date")
    
    # Display data if available
    if 'data' in st.session_state:
        data = st.session_state.data
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Symbols", len(data))
        with col2:
            st.metric("Total Premium (Crores)", f"₹{data['Premium Traded (Crores)'].sum():.2f}")
        with col3:
            st.metric("Top Symbol", data.iloc[0]['TckrSymb'] if not data.empty else "N/A")
        
        # Data table
        st.subheader("Premium Traded Data")
        
        # Add search functionality
        search_term = st.text_input("Search Symbol", placeholder="Enter symbol name...")
        if search_term:
            filtered_data = data[data['TckrSymb'].str.contains(search_term, case=False, na=False)]
        else:
            filtered_data = data
        
        # Display table with formatting
        st.dataframe(
            filtered_data.style.format({
                'Premium Traded (Crores)': '₹{:.2f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Visualizations
        st.subheader("Visualizations")
        
        # Top 10 symbols chart
        top_10 = filtered_data.head(10)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart
            fig_bar = px.bar(
                top_10,
                x='TckrSymb',
                y='Premium Traded (Crores)',
                title='Top 10 Symbols by Premium Traded',
                labels={'Premium Traded (Crores)': 'Premium Traded (₹ Crores)'}
            )
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Pie chart
            fig_pie = px.pie(
                top_10,
                values='Premium Traded (Crores)',
                names='TckrSymb',
                title='Premium Distribution (Top 10)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Download functionality
        st.subheader("Download Data")
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"premium_traded_{st.session_state.selected_date.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
