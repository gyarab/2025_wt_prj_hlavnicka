<script setup>
import { onMounted, ref } from 'vue';

const prvky = ref([]);

async function nacist() {
    try {
        const response = await fetch('/api/prvek');
        if (!response.ok) {
            throw new Error('Chyba při načítání prvků');
        }
        prvky.value = await response.json();
    } catch (error) {
        console.error(error);
    }
}

onMounted(() => {
    nacist();
});

</script>




<template>
    <h2>Dashboard</h2>
    <ul>
        <li v-for="prvek in prvky" :key="prvek.id">
            <router-link :to="`/prvek/${prvek.id}`">{{ prvek.nazev }}</router-link>
        </li>
    </ul>
    <router-link to="/prvek/novy">Přidat nový prvek</router-link>
</template>



