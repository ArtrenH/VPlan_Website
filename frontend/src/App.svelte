<svelte:head>
    <!-- Website Info-Tags -->
    <meta name="author" content="https://github.com/ArtrenH/VPlan_Website/graphs/contributors" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta name="robots" content="NOINDEX,NOFOLLOW" />
    <meta http-equiv="content-Language" content="de" />
    <meta name="description" content="Die (garantiert bessere!!!) Alternative zur VpMobil24 App" />
    <meta name="revisit-after" content="NO" />

    <!-- Auto-Generated Icons -->
    <link rel="apple-touch-icon" sizes="180x180" href="/assets/images/icons/apple-touch-icon.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/assets/images/icons/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/assets/images/icons/favicon-16x16.png">
    <link rel="manifest" href="/assets/images/icons/site.webmanifest">
    <link rel="mask-icon" href="/assets/images/icons/safari-pinned-tab.svg" color="#121212">
    <link rel="shortcut icon" type="image/x-icon" href="/assets/images/icons/favicon.ico">
    <meta name="msapplication-TileColor" content="#121212">
    <meta name="msapplication-config" content="/assets/images/icons/browser-config.xml">
    <meta name="theme-color" content="#121212">

    <!-- Materialize -->
    <link rel="stylesheet" href="/assets/css/materialize.min.css">
    <script src="assets/js/libraries/webfont.js"></script>
    <style>
        @font-face {
            font-family: 'Material Symbols Outlined';
            font-style: normal;
            font-weight: 400;
            src: url("/assets/css/fonts/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1n-q_4MrImHCIJIZrDCvHOej.woff2") format('woff2');
            font-display: swap;
        }
        
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }
        
        :root {
            --background_color: #121212;
            --accent_color: #BB86FC;
        }
    </style>
    <link rel="stylesheet" href="/assets/css/base.css">
    <script src="assets/js/libraries/materialize.min.js" defer></script>
</svelte:head>

<script>
    navigator.serviceWorker && navigator.serviceWorker.register("assets/js/sw.js").then(function(registration) {});
    import Navbar from './lib/Navbar.svelte';
</script>

<main>
    <Navbar logged_in={true} show_preferences={true} />
</main>

<style lang="scss">
</style>