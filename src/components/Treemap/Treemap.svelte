<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import Navbar from '../Navbar.svelte';

  let svg;
  let currentRoot, currentDepth = 0;
  let colorScaleRegions = d3.scaleOrdinal(d3.schemeCategory10);
  let colorScaleTerritories = d3.scaleOrdinal(d3.schemeSet3); ;
  let colorScaleAccountTypes = d3.scaleOrdinal(d3.schemeSet3);

  async function loadData() {
    const orders = await d3.csv('data/orders.csv');
    const regions = await d3.csv('data/regions.csv');
    const customers = await d3.csv('data/customers.csv');
    const mergedData = orders.map(order => {
      const region = regions.find(region => region.Territory === order.Territory);
      const customer = customers.find(customer => customer.Territory === order.Territory);
      return {
        ...order,
        Region: region ? region.Region : 'Unknown',
        AccountType: customer ? customer['Account Type'] : 'Unknown'
      };
    });

    const regionMap = new Map();

    mergedData.forEach(d => {
      if (!regionMap.has(d.Region)) {
        regionMap.set(d.Region, { name: d.Region, children: [], value: 0, quantity: 0 });
      }
      const region = regionMap.get(d.Region);
      let territory = region.children.find(t => t.name === d.Territory);
      if (!territory) {
        territory = { name: d.Territory, children: [], value: 0, quantity: 0, region: d.Region };
        region.children.push(territory);
      }
      let accountType = territory.children.find(a => a.name === d.AccountType);
      if (!accountType) {
        accountType = { name: d.AccountType, value: 0, quantity: 0, territory: d.Territory, region: d.Region };
        territory.children.push(accountType);
      }

      const orderValue = parsePricesAndQuantities(d.ProductPricesInCP, d.Quantities);
      const quantities = d.Quantities.split(', ').map(Number).reduce((a, b) => a + b, 0);

      accountType.value += orderValue;
      accountType.quantity += quantities;
      territory.value += orderValue;
      territory.quantity += quantities;
      region.value += orderValue;
      region.quantity += quantities;
    });

    return { name: "Root", children: Array.from(regionMap.values()) };
  }

  function updateTreemap(rootData, depth) {
    currentRoot = rootData;
    currentDepth = depth;

    svg.selectAll('*').remove();
    const root = d3.hierarchy(rootData)
      .eachBefore(d => d.data.id = (d.parent ? d.parent.data.id + '.' : '') + d.data.name)
      .sum(d => d.value)
      .sort((a, b) => b.value - a.value);

    const treemap = d3.treemap().size([960, 600]).padding(1).round(true);
    treemap(root);

    const nodes = depth !== null ? root.descendants().filter(d => d.depth === depth) : root.children;

    if (!colorScaleTerritories) {
      colorScaleTerritories = d3.scaleLinear()
        .domain([0, d3.max(nodes, d => d.value)])
        .range(['lightblue', 'darkblue']);
    }

    const leaf = svg.selectAll('g')
      .data(nodes)
      .join('g')
      .attr('transform', d => `translate(${d.x0},${d.y0})`);

    leaf.append('rect')
      .attr('id', d => d.data.id)
      .attr('fill', d => {
        if (depth === 0) return colorScaleRegions(d.data.id);
        else if (depth === 1) return colorScaleTerritories(d.value);
        else return colorScaleAccountTypes(d.data.id);
      })
      .attr('width', d => d.x1 - d.x0)
      .attr('height', d => d.y1 - d.y0);

    leaf.append('text')
      .attr('x', 5)
      .attr('y', '1.1em')
      .text(d => d.data.name);

    setupTooltips(leaf);

    leaf.on('click', (event, d) => {
      if (depth < 2) updateTreemap(d.data, depth + 1);
    });

  }

  function addBackButton() {
    d3.select('#backButton').on('click', () => {
      if (currentDepth > 0) updateTreemap(currentRoot, currentDepth - 1);
    });
  }

  function setupTooltips(leaf) {
    leaf.on('mouseover', (event, d) => {
      const tooltip = d3.select('#tooltip');
      tooltip.style('opacity', 1)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY + 10) + 'px')
        .html(`
          <strong>Region:</strong> ${d.data.region || ''}<br>
          <strong>Territory:</strong> ${d.data.territory || ''}<br>
          <strong>Account Type:</strong> ${d.data.name}<br>
          <strong>Order Quantity:</strong> ${d.data.quantity}<br>
          <strong>Order Value:</strong> ${d.data.value.toFixed(2)}
        `);
    }).on('mousemove', event => {
      d3.select('#tooltip')
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY + 10) + 'px');
    }).on('mouseout', () => {
      d3.select('#tooltip').style('opacity', 0);
    });
  }

  function parsePricesAndQuantities(prices, quantities) {
    const priceArray = prices.split(', ').map(Number);
    const quantityArray = quantities.split(', ').map(Number);
    return priceArray.reduce((acc, price, index) => acc + (price * quantityArray[index]), 0);
  }

  onMount(async () => {
    const hierarchicalData = await loadData();
    svg = d3.select('#treemap').append('svg')
            .attr('width', 960)
            .attr('height', 600)
            .style('font', '10px sans-serif');
    updateTreemap(hierarchicalData, 0);
    addBackButton();

  });
</script>



<Navbar />

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





