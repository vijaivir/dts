import * as React from 'react';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';

export default function ButtonAppBar({username}) {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar sx={{display: 'flex', justifyContent: 'space-between'}}>
            <h2>Day Trading</h2>
            <div style={{}}>
                {username !== '' && <h3>{username}</h3>}
            </div>
        </Toolbar>
      </AppBar>
    </Box>
  );
}