import streamlit as st
from nselib import derivatives
import pandas as pd
import logging
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="NSE Premium Traded Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .analysis-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

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

def create_advanced_metrics(data):
    """Create advanced analytical metrics"""
    if data.empty:
        return {}
    
    total_premium = data['Premium Traded (Crores)'].sum()
    top_5_premium = data.head(5)['Premium Traded (Crores)'].sum()
    concentration_ratio = (top_5_premium / total_premium) * 100 if total_premium > 0 else 0
    
    return {
        'total_premium': total_premium,
        'avg_premium': data['Premium Traded (Crores)'].mean(),
        'median_premium': data['Premium Traded (Crores)'].median(),
        'concentration_ratio': concentration_ratio,
        'gini_coefficient': calculate_gini(data['Premium Traded (Crores)'].values)
    }

def calculate_gini(values):
    """Calculate Gini coefficient for concentration analysis"""
    if len(values) == 0:
        return 0
    
    sorted_values = np.sort(values)
    n = len(values)
    cumsum = np.cumsum(sorted_values)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0

def create_enhanced_visualizations(data):
    """Create enhanced visualizations with better styling"""
    if data.empty:
        return None, None, None
    
    # Color palette
    colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
    
    top_10 = data.head(10)
    
    # Enhanced Bar Chart
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=top_10['TckrSymb'],
        y=top_10['Premium Traded (Crores)'],
        marker=dict(
            color=colors[:len(top_10)],
            line=dict(color='rgba(0,0,0,0.1)', width=1)
        ),
        text=top_10['Premium Traded (Crores)'].round(2),
        textposition='auto',
        hovertemplate='<b>%{x}</b><br>Premium: ₹%{y:.2f} Cr<extra></extra>'
    ))
    
    fig_bar.update_layout(
        title={
            'text': '🏆 Top 10 Symbols by Premium Traded',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title="Symbol",
        yaxis_title="Premium Traded (₹ Crores)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(tickangle=-45, gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        showlegend=False
    )
    
    # Enhanced Pie Chart
    fig_pie = go.Figure()
    fig_pie.add_trace(go.Pie(
        labels=top_10['TckrSymb'],
        values=top_10['Premium Traded (Crores)'],
        hole=0.4,
        marker=dict(colors=colors[:len(top_10)], line=dict(color='#FFFFFF', width=2)),
        textinfo='label+percent',
        textposition='auto',
        hovertemplate='<b>%{label}</b><br>Premium: ₹%{value:.2f} Cr<br>Share: %{percent}<extra></extra>'
    ))
    
    fig_pie.update_layout(
        title={
            'text': '🥧 Premium Distribution (Top 10)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
    )
    
    # Concentration Analysis Chart
    cumulative_data = data.copy()
    cumulative_data['Cumulative Premium'] = cumulative_data['Premium Traded (Crores)'].cumsum()
    cumulative_data['Cumulative %'] = (cumulative_data['Cumulative Premium'] / cumulative_data['Premium Traded (Crores)'].sum()) * 100
    cumulative_data['Rank'] = range(1, len(cumulative_data) + 1)
    
    fig_concentration = go.Figure()
    fig_concentration.add_trace(go.Scatter(
        x=cumulative_data['Rank'][:20],
        y=cumulative_data['Cumulative %'][:20],
        mode='lines+markers',
        name='Cumulative Premium %',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#764ba2'),
        hovertemplate='Rank: %{x}<br>Cumulative: %{y:.1f}%<extra></extra>'
    ))
    
    fig_concentration.update_layout(
        title={
            'text': '📊 Market Concentration Analysis',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title="Symbol Rank",
        yaxis_title="Cumulative Premium %",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)'),
        showlegend=False
    )
    
    return fig_bar, fig_pie, fig_concentration

def main():
    # Modern Header
    st.markdown("""
    <div class="main-header">
        <h1>📈 NSE Premium Traded Dashboard</h1>
        <p>Advanced Analytics for F&O Premium Trading Data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <h3>⚙️ Control Panel</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Date picker with better styling
        selected_date = st.date_input(
            "📅 Select Date",
            value=date(2025, 7, 7),
            help="Select the date for which you want to view premium traded data",
            max_value=date.today()
        )
        
        # Quick date buttons
        st.markdown("**Quick Select:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Today", use_container_width=True):
                selected_date = date.today()
        with col2:
            if st.button("Yesterday", use_container_width=True):
                selected_date = date.today() - timedelta(days=1)
        
        # Fetch data button
        fetch_clicked = st.button("🚀 Fetch Data", type="primary", use_container_width=True)
        
        # Analysis options
        st.markdown("---")
        st.markdown("**📊 Analysis Options:**")
        show_concentration = st.checkbox("Show Concentration Analysis", value=True)
        show_advanced_metrics = st.checkbox("Show Advanced Metrics", value=True)
        top_n = st.slider("Top N symbols to display", 5, 50, 10)
    
    # Fetch data
    if fetch_clicked:
        with st.spinner("🔄 Fetching data..."):
            data = get_premium_traded_data(selected_date)
            
            if data is not None and not data.empty:
                st.session_state.data = data
                st.session_state.selected_date = selected_date
                st.success(f"✅ Data loaded successfully for {selected_date.strftime('%d-%m-%Y')}")
            else:
                st.error("❌ No data available for the selected date")
    
    # Display data if available
    if 'data' in st.session_state:
        data = st.session_state.data
        
        # Enhanced Metrics Cards
        metrics = create_advanced_metrics(data)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Symbols</div>
                <div class="metric-value">{len(data)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Premium</div>
                <div class="metric-value">₹{metrics['total_premium']:.1f}Cr</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Top 5 Concentration</div>
                <div class="metric-value">{metrics['concentration_ratio']:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Market Leader</div>
                <div class="metric-value">{data.iloc[0]['TckrSymb'] if not data.empty else "N/A"}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Advanced Metrics Section
        if show_advanced_metrics:
            st.markdown("---")
            st.markdown("### 🔍 Advanced Analytics")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="analysis-card">
                    <h4>📈 Statistical Summary</h4>
                    <p><strong>Average Premium:</strong> ₹{metrics['avg_premium']:.2f} Cr</p>
                    <p><strong>Median Premium:</strong> ₹{metrics['median_premium']:.2f} Cr</p>
                    <p><strong>Gini Coefficient:</strong> {metrics['gini_coefficient']:.3f}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="analysis-card">
                    <h4>🎯 Market Insights</h4>
                    <p><strong>Market Concentration:</strong> {"High" if metrics['concentration_ratio'] > 70 else "Moderate" if metrics['concentration_ratio'] > 50 else "Low"}</p>
                    <p><strong>Distribution:</strong> {"Highly Skewed" if metrics['gini_coefficient'] > 0.7 else "Moderately Skewed" if metrics['gini_coefficient'] > 0.5 else "Balanced"}</p>
                    <p><strong>Active Symbols:</strong> {len(data[data['Premium Traded (Crores)'] > 1])}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Enhanced Search and Filter
        st.markdown("---")
        st.markdown("### 🔍 Data Explorer")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("🔍 Search Symbol", placeholder="Enter symbol name...")
        with col2:
            min_premium = st.number_input("Min Premium (Cr)", min_value=0.0, value=0.0, step=0.1)
        with col3:
            max_premium = st.number_input("Max Premium (Cr)", min_value=0.0, value=float(data['Premium Traded (Crores)'].max()), step=0.1)
        
        # Apply filters
        filtered_data = data.copy()
        if search_term:
            filtered_data = filtered_data[filtered_data['TckrSymb'].str.contains(search_term, case=False, na=False)]
        
        filtered_data = filtered_data[
            (filtered_data['Premium Traded (Crores)'] >= min_premium) & 
            (filtered_data['Premium Traded (Crores)'] <= max_premium)
        ]
        
        # Enhanced Data Table
        st.markdown("#### 📋 Premium Traded Data")
        
        # Add ranking column
        filtered_data_display = filtered_data.copy()
        filtered_data_display.insert(0, 'Rank', range(1, len(filtered_data_display) + 1))
        filtered_data_display['Premium Traded (Crores)'] = filtered_data_display['Premium Traded (Crores)'].round(2)
        
        st.dataframe(
            filtered_data_display.style.format({
                'Premium Traded (Crores)': '₹{:.2f}'
            }).background_gradient(subset=['Premium Traded (Crores)'], cmap='Blues'),
            use_container_width=True,
            height=400
        )
        
        # Enhanced Visualizations
        st.markdown("---")
        st.markdown("### 📊 Visual Analytics")
        
        fig_bar, fig_pie, fig_concentration = create_enhanced_visualizations(filtered_data)
        
        if fig_bar and fig_pie:
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Concentration analysis
            if show_concentration and fig_concentration:
                st.plotly_chart(fig_concentration, use_container_width=True)
        
        # Enhanced Download Section
        st.markdown("---")
        st.markdown("### 💾 Export Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"premium_traded_{st.session_state.selected_date.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            excel_buffer = pd.ExcelWriter('temp.xlsx', engine='openpyxl')
            filtered_data.to_excel(excel_buffer, index=False, sheet_name='Premium Data')
            excel_buffer.close()
            
            st.download_button(
                label="📊 Download Excel",
                data=open('temp.xlsx', 'rb').read(),
                file_name=f"premium_traded_{st.session_state.selected_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col3:
            json_data = filtered_data.to_json(orient='records', indent=2)
            st.download_button(
                label="🔗 Download JSON",
                data=json_data,
                file_name=f"premium_traded_{st.session_state.selected_date.strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

if __name__ == "__main__":
    main()