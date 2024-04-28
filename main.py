import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Quando winrate for > que 50% pintar de verde ao contrário vermelho
# Tela de input de scrim colocar filtros de Data, Vitória, Pick de herói
# Tela de players adversários com jogadores dos outros times (repetir função da Midas)
# Incluir botão de downloads das planilhas
# Telas de Time/Players/Adversários: colocar opção 'Outros' e permitir input de link do Dotabuff do usuário (arrumar link com /heroes?date=month)

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
    "Rdo": {
        "url": "https://www.dotabuff.com/players/119315361/matches?date=month&enhance=overview",
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
    data = {
        'df_pub': [],
        'df_esports': []
    }
    sides = ['radiant', 'dire']
    clean_url = url_base.split('matches')[0].rstrip('?')
    urls = {
        'df_pub': url_base,
        'df_esports': url_base.replace('/players/', '/esports/players/')
    }
    player_role = player_role

    for key, base_url in urls.items():
        for side in sides:
            url = f"{base_url}&faction={side}"
        
            while True:
                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')
                table = soup.find('table')

                if not table:
                    break
                if key =='df_pub':
                    for tr in table.find('tbody').find_all('tr'):
                        hero_cell = tr.find_all('td')[1]
                        hero_name = hero_cell.find('a').text.strip()
                        result_cell = tr.find_all('td')[3]
                        result = result_cell.find('a').text.strip()
                        icons = tr.find_all('td')[2].find_all('i', rel='tooltip')

                        lane = ""
                        role = ""
                        for icon in icons:
                            if 'lane-icon' in icon['class']:
                                lane = icon['class'][1].split('-')[2]
                            if 'role-icon' in icon['class']:
                                role = icon['class'][1].split('-')[2]

                        data[key].append([hero_name, result, lane, role, side.capitalize()])
                else:
                    for tr in table.find('tbody').find_all('tr'):
                        cells = tr.find_all('td')
                        hero_name = cells[2].text.strip()
                        matches = cells[3].text.strip()
                        win_percentage = cells[4].text.strip()

                        data[key].append([hero_name, matches, win_percentage, side.capitalize()])

                # Paginação
                next_page = soup.find('a', rel='next')
                if next_page:
                    url = 'https://www.dotabuff.com' + next_page['href']
                else:
                    break

    for key in data:
        if data[key]:
            if key == 'df_pub':
                df = pd.DataFrame(data[key], columns=['Hero', 'Result', 'Lane', 'Role', 'Faction'])
                df = clean_player_df(df, player_role)
            else:
                df = pd.DataFrame(data[key], columns=['Hero', 'Matches', 'Win %', 'Faction'])
            data[key] = df
        else:
            data[key] = None

    return data

def get_player_data_enemy(url_base):
    # Quando o player for core ignorar partida de sup e vice-versa
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

                lane = ""
                role = ""
                for icon in icons:
                    if 'lane-icon' in icon['class']:
                        lane = icon['class'][1].split('-')[2]
                    if 'role-icon' in icon['class']:
                        role = icon['class'][1].split('-')[2]

                all_data.append([hero_name, result, lane, role, side.capitalize()])

            # Paginação
            next_page = soup.find('a', rel='next')
            if next_page:
                url = 'https://www.dotabuff.com' + next_page['href']
            else:
                break

    if all_data:
        df = pd.DataFrame(all_data, columns=['Hero', 'Result', 'Lane', 'Role', 'Faction'])
        df = clean_player_df(df)
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
        
    df['Total Matches'] = 1
    df['Won Match'] = (df['Result'] == 'Won Match').astype(int)
    df['Lost Match'] = (df['Result'] == 'Lost Match').astype(int)
    df['Core'] = (df['Role'] == 'core').astype(int)
    df['Safelane'] = (df['Lane'] == 'safelane').astype(int)
    df['Midlane'] = (df['Lane'] == 'midlane').astype(int)
    df['Offlane'] = (df['Lane'] == 'offlane').astype(int)
    df['Roaming'] = (df['Lane'] == 'roaming').astype(int)
    df['Support'] = (df['Role'] == 'support').astype(int)

    cleaned_df = df.groupby('Hero').agg({
        'Total Matches': 'sum',
        'Won Match': 'sum',
        'Lost Match': 'sum',
    }).reset_index()
    cleaned_df['Vitórias/Derrota'] = cleaned_df.apply(lambda row: f"{row['Won Match']} - {row['Lost Match']}", axis=1)
    cleaned_df['Win %'] = (cleaned_df['Won Match'] / cleaned_df['Total Matches']) * 100
    cleaned_df['Win %'] = cleaned_df['Win %'].apply(lambda x: f"{x:.2f}%")
    cleaned_df = cleaned_df.sort_values(by='Total Matches', ascending=False)
    cleaned_df.drop(['Won Match', 'Lost Match'], axis=1, inplace=True)

    return cleaned_df

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

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Most banned heroes by {team_choice}:")
                st.write(ban_data.to_html(escape=False, index=False), unsafe_allow_html=True)
            with col2:
                st.write(f"Most banned heroes against {team_choice}:")
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
            player_stats = get_player_data(url, player_role)
            st.write(f"Estatísticas do(a) {player_choice} no último mês:")

            col1, col2 = st.columns([2, 1], gap="large")

            with col1:
                st.subheader("Jogos Públicos")
                if player_stats['df_pub'] is not None:
                    st.write(player_stats['df_pub'].to_html(escape=False, index=False), unsafe_allow_html=True)
                else:
                    st.write("Sem informações disponíveis para jogos públicos.")

            with col2:
                st.subheader("Jogos Oficiais")
                if player_stats['df_esports'] is not None:
                    st.write(player_stats['df_esports'].to_html(escape=False, index=False), unsafe_allow_html=True)
                else:
                    st.write("Sem informações disponíveis para jogos eSports.")
                    
        except Exception as e:
            st.error(f"Erro ao buscar dados: {str(e)}")

def show_enemy_players(players_enemy):
    st.title('Estatísticas dos jogadores adversários')
    enemy_player_list = list(players_enemy.keys()) + ['Outros']
    player_choice = st.selectbox('Escolha o(a) jogador(a):', enemy_player_list)

    if player_choice == 'Outros':
        url = st.text_input('Insira o link de perfil do Dotabuff referente ao jogador:')
    else:
        url = players_enemy[player_choice]

    url = url.replace('all','month')
    if st.button('Buscar dados'):
        try:
            player_stats = get_player_data(url)
            st.write(f"Estatísticas do(a) adversário no último mês:")

            st.subheader("Jogos Públicos")
            if player_stats['df_pub'] is not None:
                st.write(player_stats['df_pub'].to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.write("Sem informações disponíveis para jogos públicos.")

            st.subheader("Jogos Profissionais")
            if player_stats['df_esports'] is not None:
                st.write(player_stats['df_esports'].to_html(escape=False, index=False), unsafe_allow_html=True)
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
        show_enemy_players(players_enemy)
    else:
        st.write(f"{app_mode} ainda não está disponível no App.")

if __name__ == "__main__":
    main()
