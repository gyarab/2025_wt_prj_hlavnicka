<script setup>
    import { RouterLink, RouterView } from "vue-router";
</script>


<template>
    <header>
        <h1>contextum</h1>
        <RouterLink to="/">Dashboard</RouterLink>
        <RouterLink to="/prvek/1">Detail Prvku</RouterLink>
    </header>
    <main>
        <RouterView />
    </main>
</template>

