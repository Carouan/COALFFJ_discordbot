# COALFFJ_discordbot
Bot Discord en Python pour envoyer un résumé quotidien des messages par mail.


This bot is designed to send daily email reports of messages from specific channels in a Discord server.
It uses the discord.py library to interact with the Discord API and the smtplib library to send emails.


<div style="width:70%; margin:20px auto; border:2px double #A32C39; border-radius:25px; padding:10px; text-align:center; background:#fff;">

    <!-- Première rangée : Coalition Feminist for Justice + Femmes de droit -->
    <table border="0" cellspacing="0" cellpadding="0" width="100%" style="border-collapse:collapse;">
        <tr>
        <!-- Coalition sur la gauche -->
        <td style="vertical-align:middle; width:20%; text-align:center; padding:1px;">
            <a href="https://femmesdedroit.be/nos-actions/coalition-feminists-for-justice/" title="Coalition Feminist for Justice" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2024/11/Logo-FfJ.png?w=499&ssl=1" alt="Coalition Feminist for Justice" width="160" style="margin-bottom:0px;" />
            </a>
        </td>
        <td style="vertical-align:middle; width:30%; padding:2px;">
            <p style="margin:2px 0; font-weight:bold; color:#a32c39; font-size:26px; text-align:center;">
            Coalition Feminist for Justice
            </p>
        </td>
        <!-- Femmes de droit sur la droite -->
        <td style="vertical-align:middle; width:30%; text-align:center; padding:1px;">
            <p style="margin:1px 0; font-weight:bold; font-style: italic; color:#333; font-size:14px; text-align:center;">
            Portée par Femmes de droit
            </p>
            <a href="https://femmesdedroit.be/" title="Femmes de droit" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2018/04/cropped-FDD-AVATAR-Rond-RVB.jpg?w=240&ssl=1" alt="Femmes de droit" width="130" style="margin-bottom:0px;" />
            </a>
        </td>
        </tr>
    </table>

    <!-- Titre "Associations partenaires" si souhaité -->
    <p style="font-weight:bold; color:#333; font-size:18px; margin:0px; padding:0px;">
        Associations partenaires :
    </p>
    <!-- Deuxième rangée : 6 logos -->
    <table border="0" cellspacing="0" cellpadding="0" width="100%" style="border-collapse:collapse; padding:0; margin:0;">
        <tr>
        <!-- GAMS -->
        <td style="width:16.66%; text-align:center; padding:0; margin:0; border:1px">
            <a href="https://gams.be/" title="Le GAMS Belgique" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/LogoGAMS201-transparent-002.jpg?resize=1024%2C365&ssl=1" alt="Le GAMS Belgique" width="140" style="display:block; margin:0 auto;" />
            </a>
        </td>
        <!-- JUMP -->
        <td style="width:16.66%; text-align:center; padding:1px;">
            <a href="https://jump.eu.com/" title="JUMP" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/jump-for-equality.png?w=684&ssl=1" alt="JUMP" width="140" style="display:block; margin:0 auto;" />
            </a>
        </td>
        <!-- MEFH -->
        <td style="width:16.66%; text-align:center; padding:1px;">
            <a href="https://m-egalitefemmeshommes.be/" title="Le Mouvement pour l’Égalité entre les Femmes et les Hommes" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/MEFH.jpeg?resize=300%2C245&ssl=1" alt="MEFH" width="100" style="display:block; margin:0 auto;" />
            </a>
        </td>
        <!-- Université des femmes -->
        <td style="width:16.66%; text-align:center; padding:1px;">
            <a href="https://www.universitedesfemmes.be/" title="L'Université des femmes" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2023/03/UF_Capture.png?fit=237%2C73&ssl=1" alt="Université des femmes" width="150" style="display:block; margin:0 auto;" />
            </a>
        </td>
        <!-- Collectif des femmes -->
        <td style="width:16.66%; text-align:center; padding:1px;">
            <a href="https://www.collectifdesfemmes.be/" title="Le Collectif des femmes" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/Logo-CDF-court-mauve.png?resize=300%2C300&ssl=1" alt="Le Collectif des femmes" width="140" style="display:block; margin:0 auto;" />
            </a>
        </td>
        <!-- FACES -->
        <td style="width:16.66%; text-align:center; padding:1px;">
            <a href="https://www.facebook.com/people/R%C3%A9seau-FACES/100055148357144/" title="Le réseau FACES" target="_blank">
            <img src="https://i0.wp.com/femmesdedroit.be/wp-content/uploads/2025/01/FACES.jpg?resize=244%2C300&ssl=1" alt="Le réseau FACES" width="120" style="display:block; margin:0 auto;" />
            </a>
        </td>
        </tr>
    </table>
    <!-- Dernière ligne : lien de désabonnement, infos -->
    <hr style="border:none; border-top:1px solid #CCC; margin:10px 0;" />
    <p style="font-size:14px; color:#777; margin:5px;">
        <a href="http://votre-lien-de-desabonnement" style="color:#A32C39; text-decoration:none;">Se désabonner</a> - ----- - <a href="mailto:secretariat@femmesdedroit.be?&subject=Petit%20soucis%20avec%20le%20bot%20Discord%20de%20la%20coalition%20FFJ&body=Problème%20concernant%20le%20bot%20Discord%20de%20la%20coalition%20FFJ" target="_top"><strong>Contact :</strong>secretariat@femmesdedroit.be</a>
    </p>
    </div>















