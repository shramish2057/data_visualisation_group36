<script>
    import { onMount } from 'svelte';
    import * as d3 from 'd3';
    import Navbar from '../Navbar.svelte';
  
    let data;
  
    onMount(async () => {
      const response = await fetch('data/hierarchical_data.json');
      data = await response.json();
  
      const width = 960;
      const height = 600;
      const svg = d3.select("#treemap")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("font", "10px sans-serif");
  
      const treemap = d3.treemap()
        .size([width, height])
        .padding(1)
        .round(true);
  
      const root = d3.hierarchy(data)
        .sum(d => d.value)
        .sort((a, b) => b.height - a.height || b.value - a.value);
  
      treemap(root);
  
      const leaf = svg.selectAll("g")
        .data(root.leaves())
        .join("g")
        .attr("transform", d => `translate(${d.x0},${d.y0})`);
  
      leaf.append("rect")
        .attr("id", d => d.data.name)
        .attr("fill", d => d3.scaleOrdinal(d3.schemeCategory10)(d.parent.data.name))
        .attr("width", d => d.x1 - d.x0)
        .attr("height", d => d.y1 - d.y0);
  
      leaf.append("text")
        .attr("x", 5)
        .attr("y", 20)
        .text(d => d.data.name);
    });
</script>
  
<Navbar />
  
<div id="treemap"></div>
  
<style>
    #treemap svg {
        margin: 0 auto;
        display: block;
        background-color: #f4f4f4;
    }
</style>
  