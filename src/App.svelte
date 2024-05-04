<script>
	import { Router, Route } from 'svelte-routing';
	import Home from './components/Home.svelte';
	import Treemap from './components/Treemap/Treemap.svelte';
  	import BranchLeafMap from './components/BranchLeafMap/BranchLeafMap.svelte';
</script>

<main>
	<Router>
		<Route path="/" component={Home} />
		<Route path="/treemap" component={Treemap} />
	</Router>  
</main>

<style>
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}
</style>