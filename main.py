import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Quando winrate for > que 50% pintar de verde ao contrário vermelho
# Tela de input de scrim colocar filtros de Data, Vitória, Pick de herói
# Tela de players adversários com jogadores dos outros times (repetir função da Midas)
# Incluir botão de downloads das planilhas
# Telas de Time/Players/Adversários: colocar opção 'Outros' e permitir input de link do Dotabuff do usuário (arrumar link com /heroes?date=month)
# Guarda no cache a planilha para sempre ter acesso à uma
# Open DOta API

# Definindo os times/players e URLs
teams = {
    "Midas Club": "https://www.dotabuff.com/esports/teams/7913999-midas-club/heroes?date=month",
    "Acatsuki": "https://www.dotabuff.com/esports/teams/9352634-acatsuki/heroes?date=month",
    "BOOM": "https://www.dotabuff.com/esports/teams/7732977-boom-esports/heroes?date=month",
    "Estar Backs": "https://www.dotabuff.com/esports/teams/9381358-estar-backs/heroes?date=month",
    "Heroic": "https://www.dotabuff.com/esports/teams/9303484-heroic/heroes?date=month",
    "Leviatan": "https://www.dotabuff.com/esports/teams/9337731-leviatan/heroes?date=month",
    "Pacific": "https://www.dotabuff.com/esports/teams/8367062-pacific/heroes?date=month"
}

players = {
    "Costabile": {
        "url": "https://www.dotabuff.com/players/86822085/matches?date=month&enhance=overview",
        "role": "Carry"
    },
    "4dr": {
        "url": "https://www.dotabuff.com/players/85937380/matches?date=month&enhance=overview",
        "role": "Mid"
    },
    "fcr": {
        "url": "https://www.dotabuff.com/players/107579895/matches?date=month&enhance=overview",
        "role": "Offlane"
    },
    "Grd": {
        "url": "https://www.dotabuff.com/players/84853828/matches?date=month&enhance=overview",
        "role": "Support"
    },
    "hyko": {
        "url": "https://www.dotabuff.com/players/85312703/matches?date=month&enhance=overview",
        "role": "Support"
    }
}

players_enemy = {

}

def get_html_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.content, 'html.parser')
    else:
        st.error("Failed to retrieve data.")
        return None

def get_data(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', {'class': 'sortable'})

    if len(tables) < 3:
        raise ValueError("Expected at least three sortable tables but found less.")

    hero_table = pd.read_html(str(tables[0]))[0]
    hero_table.columns = hero_table.columns.droplevel(0)
    hero_table.drop('Unnamed: 0_level_1', axis=1, inplace=True)
    hero_table['Hero'] = hero_table['Hero'].str.replace(r"\d{4}-\d{2}-\d{2}$", "", regex=True)
    hero_table = hero_table.iloc[:12]

    ban_table = pd.read_html(str(tables[1]))[0]
    ban_table.columns = ['Icon', 'Hero', 'Bans', 'Win %']
    ban_table.drop('Icon', axis=1, inplace=True)

    loss_table = pd.read_html(str(tables[2]))[0]
    loss_table.columns = ['Icon', 'Hero', 'Bans', 'Loss %']
    loss_table.drop('Icon', axis=1, inplace=True)

    return hero_table, ban_table, loss_table

def get_player_data(url_base, player_role):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    all_data = []
    sides = ['radiant', 'dire']

    for side in sides:
        url = f"{url_base}&faction={side}"
        while True:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table')

            if not table:
                break

            for tr in table.find('tbody').find_all('tr'):
                hero_cell = tr.find_all('td')[1]
                hero_name = hero_cell.find('a').text.strip()
                result_cell = tr.find_all('td')[3]
                result = result_cell.find('a').text.strip()
                icons = tr.find_all('td')[2].find_all('i', rel='tooltip')
                type_cell = tr.find_all('td')[4]
                match_type = type_cell.text.strip()

                match_type = match_type.replace("All Pick", "").replace("Captains Mode", "").replace("Ability Draft", "").replace("Turbo", "").strip()

                lane = ""
                role = ""
                for icon in icons:
                    if 'lane-icon' in icon['class']:
                        lane = icon['class'][1].split('-')[2]
                    if 'role-icon' in icon['class']:
                        role = icon['class'][1].split('-')[2]

                print(f"Faction: {side} Hero: {hero_name}, Result: {result}, Type: {match_type}, Lane: {lane}, Role: {role}")
                all_data.append([match_type, hero_name, result, lane, role, side])

            # Paginação
            next_page = soup.find('a', rel='next')
            if next_page:
                url = 'https://www.dotabuff.com' + next_page['href']
            else:
                break

    if all_data:
        df = pd.DataFrame(all_data, columns=['Type', 'Hero', 'Result', 'Lane', 'Role', 'Faction'])
        df = clean_player_df(df, player_role)
        return df
    else:
        return None

def clean_player_df(df, player_role):   
    if player_role == 'Carry':
        df = df.query("Role == 'core' and Lane == 'safelane'")
    elif player_role == 'Mid':
        df = df.query("Role == 'core' and Lane == 'midlane'")
    elif player_role == 'Offlane':
        df = df.query("Role == 'core' and Lane == 'offlane'")
    elif player_role == 'Support':
        df = df.query("Role == 'support' and (Lane == 'safelane' or Lane == 'offlane' or Lane == 'roaming')")

    df_pub = df[df['Type'] == 'Ranked']
    df_esports = df[df['Type'] == 'Tournament']
    dfs = [df_pub, df_esports]

    processed_dfs = []

    for data in dfs:
        data['Total Matches'] = 1
        data['Won Match'] = (data['Result'] == 'Won Match').astype(int)
        data['Lost Match'] = (data['Result'] == 'Lost Match').astype(int)
        data['Total Radiant Matches'] = (data['Faction'] == 'radiant')
        data['Won Radiant Match'] = ((data['Faction'] == 'radiant') & (data['Result'] == 'Won Match')).astype(int)
        data['Lost Radiant Match'] = ((data['Faction'] == 'radiant') & (data['Result'] == 'Lost Match')).astype(int)
        data['Total Dire Matches'] = (data['Faction'] == 'dire')
        data['Won Dire Match'] = ((data['Faction'] == 'dire') & (data['Result'] == 'Won Match')).astype(int)
        data['Lost Dire Match'] = ((data['Faction'] == 'dire') & (data['Result'] == 'Lost Match')).astype(int)
        data['Core'] = (data['Role'] == 'core').astype(int)
        data['Safelane'] = (data['Lane'] == 'safelane').astype(int)
        data['Midlane'] = (data['Lane'] == 'midlane').astype(int)
        data['Offlane'] = (data['Lane'] == 'offlane').astype(int)
        data['Roaming'] = (data['Lane'] == 'roaming').astype(int)
        data['Support'] = (data['Role'] == 'support').astype(int)

        cleaned_data = data.groupby('Hero').agg({
            'Total Matches': 'sum',
            'Won Match': 'sum',
            'Lost Match': 'sum',
            'Total Radiant Matches': 'sum',
            'Won Radiant Match': 'sum',
            'Lost Radiant Match': 'sum',
            'Total Dire Matches': 'sum',
            'Won Dire Match': 'sum',
            'Lost Dire Match': 'sum'
        }).reset_index()
        cleaned_data['Vitórias/Derrotas'] = cleaned_data.apply(lambda row: f"{row['Won Match']} - {row['Lost Match']}", axis=1)
        cleaned_data['Win %'] = (cleaned_data['Won Match'] / cleaned_data['Total Matches']) * 100
        cleaned_data['Win %'] = cleaned_data['Win %'].apply(lambda x: f"{x:.2f}%")
        cleaned_data['Vitórias/Derrotas Radiant'] = cleaned_data.apply(lambda row: f"{row['Won Radiant Match']} - {row['Lost Radiant Match']}", axis=1)
        cleaned_data['Radiant Win %'] = (cleaned_data['Won Radiant Match'] / cleaned_data['Total Radiant Matches']) * 100
        cleaned_data['Radiant Win %'] = cleaned_data['Radiant Win %'].apply(lambda x: f"{x:.2f}%")
        cleaned_data['Vitórias/Derrotas Dire'] = cleaned_data.apply(lambda row: f"{row['Won Dire Match']} - {row['Lost Dire Match']}", axis=1)
        cleaned_data['Dire Win %'] = (cleaned_data['Won Dire Match'] / cleaned_data['Total Dire Matches']) * 100
        cleaned_data['Dire Win %'] = cleaned_data['Dire Win %'].apply(lambda x: f"{x:.2f}%")
        cleaned_data = cleaned_data.sort_values(by='Total Matches', ascending=False)
        cleaned_data.drop(['Won Match', 'Lost Match', 'Won Radiant Match', 'Lost Radiant Match', 'Won Dire Match', 'Lost Dire Match', 'Total Radiant Matches', 'Total Dire Matches'], axis=1, inplace=True)

        column_order = [
            'Hero', 'Total Matches', 'Vitórias/Derrotas', 'Win %', 'Vitórias/Derrotas Radiant', 'Radiant Win %',
            'Vitórias/Derrotas Dire', 'Dire Win %'
        ]

        cleaned_data = cleaned_data[column_order]

        processed_dfs.append(cleaned_data)
    
    return processed_dfs[0], processed_dfs[1]

def show_teams(teams):
    st.title('Estatísticas dos times')
    team_list = list(teams.keys()) + ['Outros']
    team_choice = st.selectbox('Escolha o time:', team_list)

    if team_choice == 'Outros':
        url = st.text_input('Insira o link de perfil do Dotabuff referente ao time desejado:')
        url = f'{url}/heroes?date=month'
    else:
        url = teams[team_choice]

    if st.button('Buscar dados'):
        try:
            hero_data, ban_data, loss_data = get_data(url)
            st.write(f"Heróis mais escolhidos pelo(a) {team_choice}:")
            st.write(hero_data.to_html(escape=False, index=False), unsafe_allow_html=True)

            col1, col2 = st.columns([2, 1], gap="large")
            with col1:
                st.write(f"Heróis mais banidos pelo(a) {team_choice}:")
                st.write(ban_data.to_html(escape=False, index=False), unsafe_allow_html=True)
            with col2:
                st.write(f"Heróis mais banidos contra {team_choice}:")
                st.write(loss_data.to_html(escape=False, index=False), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Erro ao mostrar dados: {str(e)}")

def show_players(players):
    st.title('Estatísticas dos jogadores')
    player_choice = st.selectbox('Escolha o(a) jogador(a):', list(players.keys()))
    player_role = players[player_choice]['role']
    url = players[player_choice]['url']

    if st.button('Buscar dados'):
        try:
            player_stats_pub, player_stats_esports = get_player_data(url, player_role)
            st.write(f"Estatísticas do(a) {player_choice} no último mês:")

            st.subheader("Jogos Públicos")
            if player_stats_pub is not None:
                st.write(player_stats_pub.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.write("Sem informações disponíveis para jogos públicos.")

            st.subheader("Jogos Oficiais")
            if player_stats_esports is not None:
                st.write(player_stats_esports.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.write("Sem informações disponíveis para jogos eSports.")
                    
        except Exception as e:
            st.error(f"Erro ao buscar dados: {str(e)}")

def main():
    st.sidebar.title("Navegação")
    app_mode = st.sidebar.selectbox("Escolha a análise", ["Times", "Jogadores", "Adversários", "Scrims"])

    if app_mode == "Times":
        show_teams(teams)
    elif app_mode == 'Jogadores':
        show_players(players)
    elif app_mode == 'Adversários':
        st.write(f"{app_mode} ainda não está disponível no App.")
    else:
        st.write(f"{app_mode} ainda não está disponível no App.")

if __name__ == "__main__":
    main()
