<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import Navbar from '../Navbar.svelte';
  import TreemapStatic from './TreemapStatic.svelte';

  let svg;
  let currentRoot, currentDepth = 0;
  let colorScaleRegions = d3.scaleOrdinal(d3.schemeTableau10);
  let colorScaleTerritories = d3.scaleOrdinal(d3.schemeSet3); ;
  let colorScaleAccountTypes = d3.scaleOrdinal(d3.schemeSet3);

  async function loadData() {
      const orders = await d3.csv('data/orders.csv');
      const regions = await d3.csv('data/regions.csv');
      const customers = await d3.csv('data/customers.csv');

      // Mapping regions to their respective territories
      let regionMap = new Map();
      regions.forEach(region => {
          regionMap.set(region.Region, { name: region.Region, children: [], value: 0 });
      });

      // Mapping territories to their respective account types and aggregating values
      orders.forEach(order => {
          let region = regions.find(region => region.Territory === order.Territory);
          let customer = customers.find(customer => customer.Territory === order.Territory);
          if (region) {
              let regionEntry = regionMap.get(region.Region);
              let territoryEntry = regionEntry.children.find(t => t.name === order.Territory);
              if (!territoryEntry) {
                  territoryEntry = { name: order.Territory, children: [], value: 0 };
                  regionEntry.children.push(territoryEntry);
              }
              let accountTypeEntry = territoryEntry.children.find(a => a.name === customer['Account Type']);
              if (!accountTypeEntry) {
                  accountTypeEntry = { name: customer['Account Type'], value: 0 };
                  territoryEntry.children.push(accountTypeEntry);
              }
              // Assuming 'Quantities' indicates the quantity of each order
              let quantities = order.Quantities.split(', ').map(Number).reduce((a, b) => a + b, 0);
              accountTypeEntry.value += quantities;  
              territoryEntry.value += quantities; 
              regionEntry.value += quantities;     
          }
      });

      return { name: "Root", children: Array.from(regionMap.values()) };
  }

  function updateTreemap(rootData, depth) {
    currentRoot = rootData;
    currentDepth = depth;

    svg.selectAll('*').remove();
    const root = d3.hierarchy(rootData)
        .sum(d => d.value) 
        .sort((a, b) => b.value - a.value); 

    const treemap = d3.treemap()
                      .tile(d3.treemapSquarify)  
                      .size([1160, 740])
                      .paddingInner(1)  
                      .round(true);
    treemap(root);


    let nodes;
    if (depth === 0) {
        nodes = root.children;  
    } else {

        let parent = root.find(d => d.data === currentRoot);
        nodes = parent ? parent.children : [];
    }

    const leaf = svg.selectAll('g')
                    .data(nodes)
                    .enter()
                    .append('g')
                    .attr('transform', d => `translate(${d.x0},${d.y0})`);

    leaf.append('rect')
        .attr('id', d => d.data.id)
        .attr('fill', d => {
            if (depth === 0) return colorScaleRegions(d.data.name);
            else if (depth === 1) return colorScaleTerritories(d.data.name);
            else return colorScaleAccountTypes(d.data.name);
        })
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0);

    leaf.append('text')
        .attr('x', 5)
        .attr('y', '1.1em')
        .text(d => d.data.name);

    setupTooltips(leaf);

    leaf.on('click', (event, d) => {
        if (currentDepth < 2) {  
            updateTreemap(d.data, currentDepth + 1);
        }
    });
}



  function setupTooltips(leaf) {
    leaf.on('mouseover', (event, d) => {
      const tooltip = d3.select('#tooltip');
      let orderValue = d.data.value;
      let orderValueDisplay = orderValue ? orderValue.toFixed(2) : 'N/A'; 
      console.log("specific data", JSON.stringify(d.data))
      tooltip.style('opacity', 1)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY + 10) + 'px')
        .html(`
          <strong>Component:</strong> ${d.data.name}<br>
          <strong>Order Value:</strong> ${orderValueDisplay}
        `);
    }).on('mousemove', event => {
      d3.select('#tooltip')
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY + 10) + 'px');
    }).on('mouseout', () => {
      d3.select('#tooltip').style('opacity', 0);
    });
  }

  onMount(async () => {
    const hierarchicalData = await loadData();
    svg = d3.select('#treemap').append('svg')
            .attr('width', 1200)
            .attr('height', 800)
            .style('font', '10px sans-serif');
    updateTreemap(hierarchicalData, 0);

  });
</script>


<Navbar />

<h3>Treemap for Order sales and Quantity through different Regions and subsequent Territories</h3>
<TreemapStatic />
<h3>Drilldown Treemap (With Drilldown feature)</h3>
<div id="treemap">
  <div id="tooltip" style="position: absolute; opacity: 0; pointer-events: none; background: white; border: 1px solid #ccc; padding: 10px;"></div>
</div>

<style>
  #treemap svg {
    margin: 0 auto;
    margin-top: 5px;
    display: block;
    background-color: #f4f4f4;
  }
  
  #tooltip {
    position: absolute;
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 10px;
    font-size: 0.9em;
    pointer-events: none;
    transition: opacity 0.3s;
    z-index: 10;
  }
</style>





