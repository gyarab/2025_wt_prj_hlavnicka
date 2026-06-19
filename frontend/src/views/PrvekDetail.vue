<template>
  <div>
    <h2>Detail prvku</h2>
    <input type="range" min="1" max="100" v-model="hodnotaSlideru" @input="zmenSlider" />
    <p>Podrobnosti o prvku s ID: {{ $route.params.id }}</p>
    <h2>{{ nadpiszeserveru }}</h2>
    <div>
        {{ popis }}
    </div>
  </div>
</template>

<script lang="tsx">
import { defineComponent } from "vue";

export default defineComponent({
  name: "PrvekDetail",
  data() {
    return {
      hodnotaSlideru: this.$route.params.id,
      nadpiszeserveru: "Načítám data...",
      popis: "",
    };
  },
  mounted() {
    this.naciestData();
  },
  methods: {
    zmenSlider() {
      this.$router.push(`/prvek/${this.hodnotaSlideru}`);
      this.naciestData();
    },
    naciestData() {
      fetch("/api/prvek/" + this.$route.params.id)
        .then((response) => response.json())
        .then((data) => {
          this.nadpiszeserveru = data.nazev;
          this.popis = data.obsah;
        })
        .catch((error) => {
          console.error("Chyba při načítání dat:", error);
          this.nadpiszeserveru = "Chyba při načítání dat";
        });
    },
  },
});
</script>