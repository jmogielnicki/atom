"use babel";
import React from 'react';
import {Entity, EntityName} from './Structure';

export class StatusBar extends React.Component {
    handleClick(e, entities) {
        if (e.button == 2) {
            
        }
    }
    render() {
        const style = {
            //borderRadius: 8,
            border: '1px solid rgba(100, 100, 100, 0.5)',
            // Atom Material theme messes with textTransform on .btn elements
            textTransform: 'none',
            maxWidth: '240px',
            //fontSize: 'x-small',
            overflow: 'hidden',
        };
        const entities = this.props.entities.slice(0);
        entities.sort(function (a, b) {
            var lineA = a.loc? a.loc.start.line : 0;
            var lineB = b.loc? b.loc.start.line : 0;
            return lineA - lineB;
        });
        return <div className="btn-group" style={{paddingTop: '8px', paddingLeft: '5px', height: '3em'}} onMouseDown={(e) => this.handleClick(e, entities)}
            onMouseLeave={this.props.onMouseLeave}
        >{
            entities
                .map(ent => <span
                        style={style}
                        className="btn"
                        onClick={this.props.onClick}
                    >
                    <Entity entity={ent} short={true}
                        onMouseOver={this.props.onMouseOver && this.props.onMouseOver.bind(this, ent)}
                        onMouseOut={this.props.onMouseOut && this.props.onMouseOut.bind(this, ent)}
                    />
                </span>)
                .reduce((res,el) => res.concat(res.length? [' ', el] : el), [])
        }</div>;
    }
};
