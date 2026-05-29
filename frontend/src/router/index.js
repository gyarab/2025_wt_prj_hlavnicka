import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import PrvekDetail from "../views/PrvekDetail.vue";

const routes = [
    {
        path: "/",
        name: "home",
        component: Dashboard
    },
    {
        path: "/prvek/:id",
        name: "detailPrvku",
        component: PrvekDetail
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});


export default router;