<template>
    <h2>Nový Prvek</h2>
    <form @submit.prevent="pridatPrvek">
        <div>
            <label for="nazev">Název:</label>
            <input type="text" id="nazev" v-model="novyPrvek.nazev" required>
        </div>
        <div>
            <label for="popis">Popis:</label>
            <textarea id="popis" v-model="novyPrvek.popis" required></textarea>
        </div>
        <button type="submit">Přidat Prvek</button>
    </form>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const novyPrvek = ref({
    nazev: '',
    popis: ''
});

async function pridatPrvek() {
    try {
        const response = await fetch('/api/prvek/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(novyPrvek.value)
        });
        if (!response.ok) {
            throw new Error('Chyba při přidávání prvku');
        }
        router.push('/');
    } catch (error) {
        console.error(error);
    }
}
</script>
