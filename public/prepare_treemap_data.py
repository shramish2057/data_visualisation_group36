import pandas as pd
import json

regions_df = pd.read_csv('data/regions.csv')
orders_df = pd.read_csv('data/orders.csv')

orders_df['CartPriceInCP'] = pd.to_numeric(orders_df['CartPriceInCP'], errors='coerce')
territory_order_values = orders_df.groupby('Territory')['CartPriceInCP'].sum().reset_index()
territory_region_data = pd.merge(territory_order_values, regions_df, on='Territory', how='left')

territory_region_data.head()

# Create a hierarchical structure for the D3 treemap
hierarchy_data = {
    'name': 'Regions',
    'children': []
}

# Group by Region, then iterate over each group to add children nodes
for region, region_group in territory_region_data.groupby('Region'):
    region_node = {
        'name': region,
        'children': []
    }
    for _, territory_row in region_group.iterrows():
        region_node['children'].append({
            'name': territory_row['Territory'],
            'value': territory_row['CartPriceInCP']
        })
    hierarchy_data['children'].append(region_node)

hierarchy_json = json.dumps(hierarchy_data, indent=2)
print(hierarchy_json[:1000])  

json_file_path = 'data/hierarchical_data.json'

with open(json_file_path, 'w') as file:
    json.dump(hierarchy_data, file, indent=2)

json_file_path

