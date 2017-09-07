"use babel";

const handlers = {
    setState(state, action) {
        return Object.assign({}, state, action.state);
    },
    indexed(state, action) {
        return Object.assign({}, state, {indexed: action.result});
    },
    setActiveFile(state, action) {
        return Object.assign({}, state, {activeFile: action.file})
    },
    setActivePosition(state, action) {
        return Object.assign({}, state, {activePosition: action.pos})
    },
    setActiveEntity(state, action) {
        return Object.assign({}, state, {
            metadata: state.metadata.map(ent => {
                return Object.assign({}, ent, {ui_active: ent == action.entity});
            })
        })
    },
    setMetadata(state, action) {
        const allMetadata = state.allMetadata || [];
        const path = action.file.path;
        const files = state.files || {};
        const key = '$' + path;
        let fixture = {};
        fixture[key] = action.file;

        const finalFiles = Object.assign({}, files, fixture);
        return Object.assign({}, state, {
            metadata: action.metadata || state.metadata,
            files: finalFiles,
            allMetadata: Object.keys(finalFiles).reduce((acc, k) => acc.concat(finalFiles[k].metadata || [] ), [])
        })
    },
    rememberPosition(state, action) {
        console.log("GO < TO", action);
        // TODO refactor
        const pos = {
            path,
            pos,
            selections: action.selections
        }
        const positions = (state.positions || []).concat(pos);
        return Object.assign({}, state, {positions})
    }
}

export default function reducer(state, action) {
    if (handlers.hasOwnProperty(action.type)) {
        return handlers[action.type](state, action);
    }
    return state;
}
