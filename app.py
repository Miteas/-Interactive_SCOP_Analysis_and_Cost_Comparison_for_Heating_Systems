import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import to_rgba
import gradio as gr
import tempfile
import os

def create_scop_table(electricity_price, gas_price, oil_price, yearly_usage):
    # Create the data
    data = {
        'SCOP': [0.5, 0.6, 0.75, 0.8, 0.9, 1, 2, 3, 4, 5],
        '1/SCOP': [2.00, 1.67, 1.33, 1.25, 1.11, 1.00, 0.50, 0.33, 0.25, 0.20],
        '1/SCOP as %': ['200%', '167%', '133%', '125%', '111%', '100%', '50%', '33%', '25%', '20%'],
        'System Type': [
            'Inefficient old boiler', 'Well functioning oil-fired range cooker',
            'Below-average oil/gas boiler', 'Moderately efficient oil/gas system',
            'Efficient gas system', 'Electric resistive heating',
            'Very-poor install heat pump', 'low-middling-install heat pump',
            'Good-install heat pump', 'Top-of-the-COPs-heat pump'
        ],
        'Fuel': ['Oil', 'Oil', 'Oil', 'Oil', 'Gas', 'Electricity', 'Electricity', 'Electricity', 'Electricity', 'Electricity'],
    }
    
    df = pd.DataFrame(data)
    
    df['Cost per kWh of heating'] = df.apply(lambda row:
        electricity_price / row['SCOP'] if row['Fuel'] == 'Electricity' else
        gas_price / row['SCOP'] if row['Fuel'] == 'Gas' else
        oil_price / row['SCOP'], axis=1)
    
    df[f'Yearly cost ({yearly_usage:,} kWh)'] = df['Cost per kWh of heating'] * yearly_usage / 100

# Increase figure size for full-width display
    fig, ax = plt.subplots(figsize=(24, 12))
    ax.axis('off')
    
    cmap_cost = LinearSegmentedColormap.from_list("", [
        "#00A000", "#40C040", "#80E080", "#FFFF80", "#FFA080", "#FF6040", "#FF2000"
    ])
    
    cell_text = df.values.tolist()
    for row in cell_text:
        row[-2] = f"{row[-2]:.1f}p"
        row[-1] = f"£{row[-1]:,.0f}"
    
    table = ax.table(cellText=cell_text, colLabels=df.columns, cellLoc='center', loc='center')
    
    table.auto_set_font_size(False)
    table.set_fontsize(20)
    
    # Adjust column widths
    table.auto_set_column_width(col=list(range(len(df.columns))))
    
    # Manually increase the width of the System Type column
    table.auto_set_column_width([df.columns.get_loc("System Type")])
    table._cells[(0, df.columns.get_loc("System Type"))].set_width(table._cells[(0, df.columns.get_loc("System Type"))].get_width() * 1.5)
    
    table.scale(1.5, 2.5)
    
    yearly_cost_column = df.columns.get_loc(f'Yearly cost ({yearly_usage:,} kWh)')
    max_cost = df[f'Yearly cost ({yearly_usage:,} kWh)'].max()
    min_cost = df[f'Yearly cost ({yearly_usage:,} kWh)'].min()
    
    for i, key in enumerate(table._cells):
        cell = table._cells[key]
        if key[0] == 0:  # Header row
            cell.set_facecolor('white')
            cell.set_text_props(weight='bold', color='black')
        else:
            yearly_cost = df[f'Yearly cost ({yearly_usage:,} kWh)'].iloc[key[0]-1]
            normalized_cost = (yearly_cost - min_cost) / (max_cost - min_cost)
            color = cmap_cost(np.power(normalized_cost, 0.6))
            rgba_color = to_rgba(color, alpha=0.7)
            cell.set_facecolor(rgba_color)
    
    #plt.title('SCOP Analysis and Cost Comparison for Heating Systems', fontsize=16, fontweight='bold', pad=20)
    
    #footnote = f"Based on electricity price of {electricity_price:.2f}p/kWh, gas price of {gas_price:.2f}p/kWh, and oil price of {oil_price:.2f}p/kWh"
    #plt.figtext(0.5, 0.01, footnote, ha='center', fontsize=15, style='italic')
    
    plt.tight_layout()
    
    # Save the figure to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
        plt.savefig(tmpfile.name, format='png', dpi=200, bbox_inches='tight')
    
    plt.close(fig)
    return tmpfile.name

# Define Gradio interface with custom layout and explanations
with gr.Blocks() as iface:
    gr.Markdown("""
    # Interactive SCOP Analysis and Cost Comparison for Heating Systems

    ## What is SCOP?
    SCOP stands for Seasonal Coefficient of Performance. It's a measure of heating system efficiency that takes into account seasonal variations in performance. SCOP represents the ratio of heat output to energy input over an entire heating season.

    ## Understanding SCOP and 1/SCOP
    - SCOP: Higher values indicate better efficiency. For example, a SCOP of 3 means the system produces 3 units of heat for every 1 unit of energy input.
    - 1/SCOP is simply the inverse of SCOP. While SCOP focuses on output, 1/SCOP can be thought of as the input energy required to produce one unit of heat.
    -Higher 1/SCOP = Lower Efficiency:
        - 1/SCOP of 0.25 (SCOP 4): Only 0.25 units of input energy are needed to produce 1 unit of heat, indicating high efficiency.
        - 1/SCOP of 0.33 (SCOP 3): 0.33 units of input energy are required to produce 1 unit of heat.
        - 1/SCOP of 0.5 (SCOP 2): 0.5 units of input energy are needed to produce 1 unit of heat, implying lower efficiency.

    Why is 1/SCOP helpful?
    Even though it might seem counterintuitive at first, 1/SCOP provides a direct way to compare the input energy requirements of different heating systems. A lower 1/SCOP signifies that less energy is needed 
    to generate the same amount of heat, leading to lower running costs and reduced environmental impact.

    ## Why This Analysis Matters
    1. Energy Efficiency: Higher SCOP values indicate more efficient systems, which use less energy to produce the same amount of heat.
    2. Cost Savings: More efficient systems typically lead to lower operating costs.
    3. Environmental Impact: Higher efficiency usually means lower carbon emissions for the same heating output.

    ## How to Use This Tool
    Adjust the sliders below to see how different energy prices and usage levels affect the annual cost of various heating systems. The table will update to show:
    - SCOP and 1/SCOP values for different systems
    - Cost per kWh of heating
    - Estimated yearly cost based on your inputs

    This tool can help you compare the efficiency and cost-effectiveness of different heating systems under various scenarios.
    """)

    with gr.Row():
        electricity_price = gr.Slider(minimum=10, maximum=40, step=0.01, value=22.36, label="Electricity Price (p/kWh)")
        gas_price = gr.Slider(minimum=2, maximum=20, step=0.01, value=5.48, label="Gas Price (p/kWh)")
        oil_price = gr.Slider(minimum=2, maximum=20, step=0.01, value=8.7, label="Oil Price (p/kWh)")
        yearly_usage = gr.Slider(minimum=5000, maximum=50000, step=100, value=20000, label="Yearly Usage (kWh)")
    
    btn = gr.Button("Generate Table")
    output_image = gr.Image(label="SCOP Analysis Table")
    
    gr.Markdown("""
    ## Interpreting the Results
    - Green colors in the table indicate lower yearly costs, while red colors indicate higher costs.
    - Compare the '1/SCOP as %' column to see how much of the input energy each system uses.
    - The 'Yearly cost' column shows the estimated annual operating cost for each system based on your inputs.

    ## Key Takeaways
    - Heat pumps (systems with high SCOP values) often have higher upfront costs but lower operating costs.
    - Traditional systems like oil boilers typically have lower SCOP values, meaning they use more energy to produce the same amount of heat.
    - The most cost-effective system can vary depending on local energy prices and usage patterns.

    Remember, this analysis focuses on operating costs. When making decisions, also consider factors like installation costs, maintenance requirements, and local climate conditions.
    """)

    inputs = [electricity_price, gas_price, oil_price, yearly_usage]
    btn.click(fn=create_scop_table, inputs=inputs, outputs=output_image)

# Launch the app
iface.launch()


# Cleanup function to remove temporary files
def cleanup(files):
    for file in files:
        try:
            os.remove(file)
        except:
            pass

# Register cleanup function to be called when the script exits
import atexit
atexit.register(cleanup, [])