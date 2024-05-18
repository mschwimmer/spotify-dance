async function fetchPlaylists() {
    try {
        const response = await fetch('/user-playlists');
        const data = await response.json();
        console.log('Playlists', data);
        return data;
    } catch (error) {
        console.error('Error fetching user playlists', error)
        throw error;
    }
}

async function fetchPlaylistItems(playlists) {
    try {
        const response = await fetch('/playlist-items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(playlists)
        });
        const data = await response.json();
        console.log('Playlist items', data);
        return data;
    } catch (error) {
        console.error('Error fetching playlist items', error)
        throw error;
    }
}

async function fetchSongList(playlists) {
    const response = await fetch('/song-list', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(playlists)
    });
    const songs = await response.json();
    console.log('Song list: ', songs);
    return songs
}

async function fetchSongData(songs) {
    const response = await fetch('/song-data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(songs)
    });
    const song_data = await response.json();
    console.log('Song data: ', song_data);
    return song_data
}

async function fetchDanceSongs(songs, song_data) {
    const response = await fetch('/dance-songs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'songs': songs, 'song_data': song_data})
    });
    const dance_songs = await response.json();
    console.log('Dance songs: ', dance_songs);
    return dance_songs
}

async function getPlaylistItems() {
    try {
        var playlists = await fetchPlaylists();
        if (playlists.length > 0) {
            playlists = await fetchPlaylistItems(playlists);
            return playlists
        } else {
            console.log('No Playlists available');
        }
    } catch (error) {
        console.error('Error Failed to get playlists or items');
    }
}

async function getSongs(playlists) {
    try {
        var songs = await fetchSongList(playlists);
        return songs
    } catch (error) {
        console.error('Error getting song list');
    }
}

async function getSongData(songs) {
    try {
        var song_data = await fetchSongData(songs);
        return song_data
    } catch (error) {
        console.error('Error getting song data');
    }
}

async function getDanceSongs(songs, song_data) {
    try {
        var dance_songs = await fetchDanceSongs(songs, song_data);
        return dance_songs
    } catch (error) {
        console.error('Error getting dance songs');
    }
}

async function performSequentialTasks() {
    try {
        const playlists = await getPlaylistItems();
        const songs = await getSongs(playlists);
        const song_data = await getSongData(songs);
        const dance_songs = await getDanceSongs(songs, song_data);
        console.log('Finished performing sequential tasks');
        return dance_songs
    } catch (error) {
        console.error('Error performing sequential tasks');
    }
}


performSequentialTasks()
    .then(dance_songs => {
        var songTable = '';
        // Create a table row for each song
        dance_songs.forEach((song, index) => {
            songTable += `
            <tr>
                <th scope="row">${index + 1}</th>
                <td>${song.track_name}</td>
                <td>${song.track_album}</td>
                <td>${song.track_artist}</td>
                <td>${song.playlist_name}</td>
                <td>${song.danceability}</td>
            </tr>`;
        });

        // Replace the existing table content
        document.querySelector('.table tbody').innerHTML = songTable;

        // Update the h1 tag in the loading message
        document.getElementById('loading-message').querySelector('h1').textContent = "Successfully retrieved your dance songs!";

        // Delete the snarky p tags
        const pTags = document.getElementById('loading-message').querySelectorAll('p');
        pTags.forEach((p) => {
        p.remove()
        });

        // Start displaying all the content in our data-container div
        document.querySelector('.data-container').style.removeProperty("display");

    });