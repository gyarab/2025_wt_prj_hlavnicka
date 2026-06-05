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
    },
    {
        path: "/:catchAll(.*)",
        name: "notFound",
        component: () => import("../views/NotFound.vue")
    },
    {
        path: "/prvek/novy",
        name: "novyPrvek",
        component: () => import("../views/NovyPrvek.vue")
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes
});


export default router;