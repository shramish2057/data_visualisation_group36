<script>
  import Navbar from '../Navbar.svelte';
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import { tick } from 'svelte';

  let businessUnits = [];
  let selectedUnit = '';
  let productLeaders = [];
  let selectedLeader = '';
  let brandNames = [];
  let selectedBrand = '';
  let data = [];
  let detailedOrderItems = [];
  let svg;
  let tooltip = { visibility: 'hidden', content: '', x: 0, y: 0 };
  let globalColorScale = d3.scaleSequential(d3.interpolateInferno)
    .domain([0, d3.max(data, d => d.value)]); 
  let showHeatmap = false; 
  let heatmapSubtype = '';
  

  onMount(async () => {
  const products = await d3.csv('data/products.csv');
  const orders = await d3.csv('data/orders.csv');

  const productLookup = products.reduce((acc, product) => {
    acc[product['Product Name'].toLowerCase()] = product;
    return acc;
  }, {});

  let aggregatedOrderItems = [];  

  orders.forEach(order => {
    let products = order.Products.split(';');
    let quantities = order.Quantities.split(',');
    let productPrices = order.ProductPricesInCP.split(',');

    products.forEach((productName, index) => {
      productName = productName.trim().toLowerCase();
      if (productLookup[productName]) {
        let product = productLookup[productName];
        detailedOrderItems.push({
          Type: product.Type,
          Subtype: product.Subtype,
          BusinessUnit: product['Business Unit'],
          ProductBusinessLineLeader: product['Products Business Line Leader'],
          BrandName: product['Brand Name'],
          Quantity: parseInt(quantities[index], 10),
          ProductPriceInCP: parseInt(productPrices[index], 10),
          OrderDate: order.OrderDate,
          ProductName: product['Product Name']
        });


        let existingItem = aggregatedOrderItems.find(item => 
          item.ProductName === product['Product Name'] && 
          item.BusinessUnit === product['Business Unit'] &&
          item.ProductBusinessLineLeader === product['Products Business Line Leader'] &&  
          item.BrandName === product['Brand Name']
        );

        if (existingItem) {
          existingItem.Quantity += parseInt(quantities[index], 10);
        } else {
          aggregatedOrderItems.push({
            Type: product.Type,
            Subtype: product.Subtype,
            BusinessUnit: product['Business Unit'],
            ProductBusinessLineLeader: product['Products Business Line Leader'],
            BrandName: product['Brand Name'],
            Quantity: parseInt(quantities[index], 10),
            ProductPriceInCP: parseInt(productPrices[index], 10),
            ProductName: product['Product Name']
          });
        }
      }
    });
  });

  let subtypeAggregation = d3.rollup(aggregatedOrderItems, 
      v => d3.sum(v, d => d.Quantity),
      d => d.Subtype.trim().toLowerCase());
  console.log("Subtype Aggregation:", Array.from(subtypeAggregation.entries()));

  aggregatedOrderItems.forEach(item => {
    let key = item.Subtype.trim().toLowerCase();
    item.subTypeQuantity = subtypeAggregation.get(key) || 0;
    console.log(`Item: ${item.ProductName}, Subtype: ${item.Subtype}, subTypeQuantity: ${item.subTypeQuantity}`);
  });

  businessUnits = Array.from(new Set(products.map(p => p['Business Unit']))).sort();
  productLeaders = Array.from(new Set(products.map(p => p['Products Business Line Leader']))).sort();
  brandNames = Array.from(new Set(products.map(p => p['Brand Name']))).sort();
  data = aggregatedOrderItems; 
  selectedUnit = '';
  selectedLeader = '';
  selectedBrand = '';


  drawChart();  
});

  onMount(async () => {
    globalColorScale = d3.scaleSequential(d3.interpolateInferno)
      .domain([0, d3.max(data, d => d.Quantity)]); 
    drawChart();
  });

  function drawLegend(colorScale) {
  const legend = svg.append("g")
    .attr("transform", "translate(100,10)"); 

  const horizontalSpacing = 280; 
  const verticalSpacing = 30;    
  const itemsPerRow = Math.floor(1600 / horizontalSpacing); 

  const legendEntries = legend.selectAll('g')
    .data(colorScale.domain())
    .enter()
    .append('g')
    .attr("transform", (d, i) => {
      const x = (i % itemsPerRow) * horizontalSpacing;
      const y = Math.floor(i / itemsPerRow) * verticalSpacing;
      return `translate(${x}, ${y})`;
    });

  legendEntries.append('rect')
    .attr('width', 18)
    .attr('height', 18)
    .attr('fill', colorScale);

  legendEntries.append('text')
    .attr('x', 24)
    .attr('y', 9)
    .attr('dy', '.35em')
    .text(d => d);
  }
  

  $: if (showHeatmap && heatmapSubtype && data.length > 0) {
    tick().then(() => {
      drawHeatmap(heatmapSubtype, selectedUnit, selectedLeader, selectedBrand);
    });
  }
  $: filteredData = data.filter(d => 
    (selectedUnit === '' || d.BusinessUnit === selectedUnit) &&
    (selectedLeader === '' || d.ProductBusinessLineLeader === selectedLeader) &&
    (selectedBrand === '' || d.BrandName === selectedBrand)
  );
  $: if (filteredData.length > 0) {
    drawChart();
  }


  function drawHeatmapLegend(colorScale) {
    const svg = d3.select("#heatmap").select("svg");
    if (!svg.node()) return;
    const svgWidth = +svg.attr("width");
    const svgHeight = +svg.attr("height") + 100; 
    svg.attr("height", svgHeight);

    const legendWidth = 500;
    const legendHeight = 20;

    const legendTransformY = svgHeight - 50; 

    const gradient = svg.append("defs")
      .append("linearGradient")
      .attr("id", "gradient")
      .attr("x1", "0%")
      .attr("x2", "100%")
      .attr("y1", "0%")
      .attr("y2", "0%");

    for (let i = 0; i <= 10; i++) {
      gradient.append("stop")
        .attr("offset", `${i / 10 * 100}%`)
        .attr("stop-color", colorScale(colorScale.domain()[0] + (colorScale.domain()[1] - colorScale.domain()[0]) * i / 10));
    }

    const legend = svg.append("g")
      .attr("transform", `translate(${(svgWidth - legendWidth) / 2}, ${legendTransformY})`);

    legend.append("rect")
      .attr("width", legendWidth)
      .attr("height", legendHeight)
      .style("fill", "url(#gradient)");

    const legendScale = d3.scaleLinear()
      .domain(colorScale.domain())
      .range([0, legendWidth]);

    const legendAxis = d3.axisBottom(legendScale).ticks(5);
    legend.append("g")
      .attr("transform", `translate(0, ${legendHeight})`)
      .call(legendAxis);
  }

  function exportChartAsImage(svgElement, backgroundColor) {
      const svgBoundingBox = svgElement.getBoundingClientRect();

      const canvas = document.createElement('canvas');
      canvas.width = svgBoundingBox.width;
      canvas.height = svgBoundingBox.height;
      const ctx = canvas.getContext('2d');

      // Set the canvas background color
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const img = new Image();
      img.onload = function() {
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          const dataUrl = canvas.toDataURL('image/png');
          const link = document.createElement('a');
          link.href = dataUrl;
          link.download = 'chart.png';
          link.click();
      };
      const svgXml = new XMLSerializer().serializeToString(svgElement);
      img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgXml)));
  }

  function handleBranchLeafMapExportClick() {
      const svgElement = document.querySelector('#branchLeafMap svg');
      exportChartAsImage(svgElement, 'white');
  }

  function handleHeatmapExportClick() {
    const svgElement = document.querySelector('#heatmap svg');
    exportChartAsImage(svgElement, 'white');
  }

  function handleClick(subtype) {
      if (showHeatmap && subtype === heatmapSubtype) {
          showHeatmap = false;
          heatmapSubtype = '';
      } else {
          showHeatmap = true;
          heatmapSubtype = subtype;
      }
      drawChart(); 
  }

  function drawChart() {
    d3.select('#branchLeafMap svg').remove();
    svg = d3.select('#branchLeafMap').append('svg')
    .attr('width', 1600)
    .attr('height', 1000);
    console.log("data", JSON.stringify(data))
    let chartYOffset = 50;
    let filteredData = data.filter(d => 
      (selectedUnit === '' || d.BusinessUnit === selectedUnit) &&
      (selectedLeader === '' || d.ProductBusinessLineLeader === selectedLeader) &&
      (selectedBrand === '' || d.BrandName === selectedBrand)
    );
    let aggregatedData = d3.rollup(filteredData, 
    v => ({
        Quantity: d3.sum(v, d => d.Quantity), 
        ProductPriceInCP: d3.sum(v, d => d.ProductPriceInCP),  
        subTypeQuantity: v[0].subTypeQuantity  
    }),
    d => d.Type, d => d.Subtype);

    let maxQuantity = d3.max(data, d => d.subTypeQuantity);
    let minQuantity = d3.min(data, d => d.subTypeQuantity);

    let colorScale = d3.scaleOrdinal(d3.schemeTableau10);
    let yScale = d3.scaleBand()
      .domain(Array.from(aggregatedData.keys()))
      .range([chartYOffset, 700]) 
      .padding(1);

    let axis = svg.append('g')
      .attr('class', 'axis')
      .attr('transform', `translate(800, ${chartYOffset})`);

    axis.call(d3.axisLeft(yScale).tickSize(0))
      .selectAll('text')
      .style('text-anchor', 'start')
      .attr('x', (d, i) => i % 2 === 0 ? 10 : -150) 
      .attr('dy', -50); 

    svg.append('g')
      .selectAll('line')
      .data(yScale.domain())
      .join('line')
      .attr('x1', 800)
      .attr('y1', d => yScale(d))
      .attr('x2', (d, i) => i % 2 === 0 ? 130 : 1470) 
      .attr('y2', d => yScale(d))
      .attr('stroke', d => colorScale(d));

    svg.append("text")
        .attr("text-anchor", "end")
        .attr("transform", "rotate(-90)")
        .attr("y", 20)
        .attr("x", -400)
        .text("Type/Subtype");

    let leafGroups = svg.append('g')
      .selectAll('g')
      .data(yScale.domain())
      .join('g')
      .attr('transform', d => `translate(800, ${yScale(d)})`);
    
    
    leafGroups.each(function(type, index) {
    let subtypes = aggregatedData.get(type);
    let shift = index % 2 === 0 ? -1 : 1;
    d3.select(this).selectAll('circle')
        .data(Array.from(subtypes.entries()))
        .join('circle')
        .attr('cx', (d, i) => shift * (i * 35 + 35))
        .attr('cy', 0)
        .attr('r', 10)
        .attr('fill', (d) => {
            let baseColor = colorScale(type);
            let hslColor = d3.hsl(baseColor);
            let intensityFactor = d3.scaleSqrt()
                .domain([minQuantity, maxQuantity])
                .range([0, 1])
                .clamp(true)(d[1].subTypeQuantity);
            hslColor.l *= intensityFactor < 0.3 ? 0.4 : (1 - intensityFactor * 0.6);
            return hslColor;
        })
        .attr('stroke', d => (showHeatmap && d[0] === heatmapSubtype) ? 'black' : 'none')
        .attr('stroke-width', 3)
        .on('click', (event, d) => {
            handleClick(d[0]); 
        })
        .on('mouseover', (event, d) => {
            tooltip = {
                visibility: 'visible',
                content: `Subtype: ${d[0]}<br/>Quantity: ${d[1].subTypeQuantity}`,
                x: event.pageX + 10,
                y: event.pageY - 10
            };
        })
        .on('mouseout', () => {
            tooltip.visibility = 'hidden';
        });
      });
    drawLegend(colorScale);
  }


  function updateChart() {
    filteredData = data.filter(d => 
      (selectedUnit === '' || d.BusinessUnit === selectedUnit) &&
      (selectedLeader === '' || d.ProductBusinessLineLeader === selectedLeader) &&
      (selectedBrand === '' || d.BrandName === selectedBrand)
    );
    drawChart();
  }


  function drawHeatmap(subtype, businessUnit, productLeader, brandName) {
  console.log("Redrawing heatmap for subtype:", subtype);
  let svg = d3.select("#heatmap svg");

  const margin = { top: 30, right: 30, bottom: 30, left: 150 };
  const width = 1000 - margin.left - margin.right;
  const height = 700 - margin.top - margin.bottom;

  if (!svg.empty()) {
    svg.selectAll("*").remove();  
  } else {
    svg = d3.select("#heatmap").append("svg");
  }
  svg.attr("width", width + margin.left + margin.right)
     .attr("height", height + margin.top + margin.bottom);

  svg = svg.append("g")
           .attr("transform", `translate(${margin.left},${margin.top})`);

  const filteredData = detailedOrderItems.filter(d =>
    d.Subtype === subtype &&
    (businessUnit === '' || d.BusinessUnit === businessUnit) &&
    (productLeader === '' || d.ProductBusinessLineLeader === productLeader) &&
    (brandName === '' || d.BrandName === brandName)
  );
const nestedData = d3.rollup(filteredData,
  v => d3.sum(v, d => d.Quantity),
  d => d.ProductName,
  d => d.OrderDate.slice(0, 4)
);

if (!filteredData.length) {
    console.log("No data to display for the heatmap.");
    return;
}

const productNames = Array.from(nestedData.keys());
const years = Array.from(new Set(filteredData.map(d => d.OrderDate.slice(0, 4)))).sort();


    const x = d3.scaleBand()
      .range([0, width])
      .domain(years)
      .padding(0.05);
    svg.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x));

    const y = d3.scaleBand()
      .range([height, 0])
      .domain(productNames)
      .padding(0.05);
    svg.append("g")
      .call(d3.axisLeft(y));

    const maxQuantity = d3.max(Array.from(nestedData.values(), typeMap => d3.max(typeMap.values())));
    const colorScale = d3.scaleSequential(d3.interpolateInferno)
      .domain([0, maxQuantity]);

    svg.append("text")
        .attr("x", 600)
        .attr("y", -100) 
        .attr("text-anchor", "middle")
        .style("font-size", "18px")
        .style("font-weight", "bold") 
        .style("fill", "#333") 
        .text("Annual Product Sales Heatmap for selected Product Subtype");

    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", -margin.left + 20)
        .attr("x", -(height / 2))
        .attr("text-anchor", "middle")
        .text("Products");

    svg.append("text")
        .attr("x", width / 2)
        .attr("y", height + margin.top + 40)
        .attr("text-anchor", "middle")
        .text("Year");

    nestedData.forEach((yearsMap, productName) => {
      yearsMap.forEach((quantity, year) => {
        svg.append("rect")
          .attr("x", x(year))
          .attr("y", y(productName))
          .attr("width", x.bandwidth())
          .attr("height", y.bandwidth())
          .style("fill", colorScale(quantity))
          .on('mouseover', (event, d) => {
            tooltip = { 
              visibility: 'visible', 
              content: `Product: ${productName}<br/>Year: ${year}<br/>Quantity: ${quantity}`, 
              x: event.pageX + 10, 
              y: event.pageY - 10 
            };
            tooltip = {...tooltip};
          })
          .on('mouseout', () => {
            tooltip.visibility = 'hidden';
            tooltip = {...tooltip};
          });
      });
    });
    drawHeatmapLegend(colorScale);
    tick(); 
  }

</script>

<Navbar />
<h1>BranchLeafMap Visualisation</h1>
<button on:click={handleBranchLeafMapExportClick}>Export BranchLeafMap as Image</button>
<div class="tiling-method-container">
  <h5>Business Units</h5>
  <select class="selection" bind:value={selectedUnit} on:change={updateChart}>
    <option value="">All</option>
    {#each businessUnits as unit}
      <option value={unit}>{unit}</option>
    {/each}
  </select>
  <h5>Product Business Line Leader</h5>
  <select class="selection" bind:value={selectedLeader} on:change={updateChart}>
    <option value="">All</option>
    {#each productLeaders as unit}
      <option value={unit}>{unit}</option>
    {/each}
  </select>
  <h5>Brand Name</h5>
  <select class="selection" bind:value={selectedBrand} on:change={updateChart}>
    <option value="">All</option>
    {#each brandNames as unit}
      <option value={unit}>{unit}</option>
    {/each}
  </select>
</div>
<h3>Product Types</h3>

<div id="branchLeafMap"></div> 

{#if showHeatmap}
  <h3>Heatmap of Annual Sales by Products for Selected Product Subtype</h3>
  <div id="heatmap"></div>
  <h4>Quantity Scale</h4>
<div id="tooltip" style="position: absolute; visibility: {tooltip.visibility}; top: {tooltip.y}px; left: {tooltip.x}px; background: lightsteelblue; padding: 5px; border-radius: 8px;">
  {@html tooltip.content}
</div>
<button on:click={handleHeatmapExportClick}>Export Heatmap as Image</button>
{/if}
<style>
  #branchLeafMap, #heatmap {
    width: 100%;
    min-height: 500px;
  }

  #tooltip {
    text-align: center;
    width: 120px;
    height: 80px;
    font: 12px sans-serif;
    border: 0px;
    pointer-events: none;
  }
  .tiling-method-container {
    display: flex; 
    align-items: center; 
    margin-bottom: 10px;
  }

  .tiling-method-container {
    display: flex;      
    justify-content: center; 
    align-items: center;
    width: 100%;         
  }

  .tiling-method-container h5 {
    margin-right: 20px;  
  }
  .selection {
    margin-right: 50px;  
  }

</style>


