<script>
    import { onMount } from 'svelte';
    
    export let logged_in = false;
    export let show_preferences = false;

    onMount(() => {
        var dropdown_elems = document.querySelectorAll('.dropdown-trigger-preferences');
        // @ts-ignore
        M.Dropdown.init(dropdown_elems, {
            coverTrigger: false,
            alignment: 'right',
            constrainWidth: false
        });
    });
</script>

<nav class="dp02">
    <div class="nav-wrapper">
        <a href="/">
            <img src="/assets/images/better_vp_white.svg" alt="Logo" width="64" height="64" class="unselectable">
        </a>
        <ul id="nav-bar" class="right">
            <li><a href="/about">Über uns</a></li>
            {#if logged_in}
            <li class="preferences-nav"><button class="dropdown-trigger-preferences" data-target="preferences-dropdown"><span class="material-symbols-outlined">tune</span></button></li>
            <ul id='preferences-dropdown' class='dropdown-content'>
                <li><a href="javascript:void(0);" data-target="settings" class="modal-trigger"><span class="material-symbols-outlined">settings</span>Einstellungen</a></li>
                {#if show_preferences}
                <li><a href="javascript:void(0);" data-target="preferences_modal" class="modal-trigger"><span class="material-symbols-outlined">account_circle</span>Unterricht wählen</a></li>
                {/if}
                <li><a href="/logout" class="waves-effect"><span class="material-symbols-outlined">logout</span>Logout</a></li>
            </ul>
            {/if}
        </ul>
    </div>
</nav>

<style lang="scss">
    nav {
        padding: 0px 20px;
        @media only screen and (max-width: 500px) {
            padding: 0px 5px !important;
        }
        margin-right: calc(100% - 100vw);
    }

    nav img {
        height: 100%;
        padding: 5px;
    }
    .preferences-nav span {
        vertical-align: middle;
    }
</style>